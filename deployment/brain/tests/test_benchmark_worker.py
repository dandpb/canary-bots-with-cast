"""Real supervised CLI worker with a synthetic private Unix datagram peer."""

import errno
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import time
from collections import deque
from pathlib import Path

import pytest
from test_protocol import observation

from canary_brain.recording import RecordingStore, ReplayReader
from canary_brain.store import Store


class SyntheticPublisher:
    """Bounded fixture producer: retry the same frozen frame or fail explicitly."""

    def __init__(self, peer, destination, timeout=2):
        self.peer, self.destination, self.timeout = peer, destination, timeout
        self.pending = deque()
        self.pending_bytes = 0
        self.issued_sequence = self.accepted_sequence = 0
        self.overflow_frames = self.discarded_frames = 0

    def enqueue(self, packet):
        sequence = None
        if packet.get("type") == "telemetry":
            self.issued_sequence += 1
            sequence = self.issued_sequence
            packet = {**packet, "sequence": sequence}
        payload = json.dumps(packet).encode()
        if len(self.pending) >= 64 or self.pending_bytes + len(payload) > 128 * 1024:
            self.overflow_frames += 1
            self.discarded_frames += 1
            raise AssertionError("synthetic producer exceeded its bounded outbox")
        self.pending.append((payload, sequence))
        self.pending_bytes += len(payload)

    def send_frozen(self, payload, *, deadline=None):
        if deadline is None:
            deadline = time.monotonic() + self.timeout
        while True:
            try:
                sent = self.peer.sendto(payload, self.destination)
            except OSError as error:
                if error.errno not in {errno.EAGAIN, errno.ENOBUFS, errno.EINTR}:
                    raise
                if time.monotonic() >= deadline:
                    raise AssertionError(
                        "synthetic producer could not drain its pending frame"
                    ) from error
                time.sleep(0.005)
                continue
            assert sent == len(payload), "a synthetic datagram was not sent atomically"
            return

    def flush(self):
        deadline = time.monotonic() + self.timeout
        while self.pending:
            payload, sequence = self.pending[0]
            self.send_frozen(payload, deadline=deadline)
            self.pending.popleft()
            self.pending_bytes -= len(payload)
            if sequence is not None:
                self.accepted_sequence = sequence

    def publish(self, packet):
        self.enqueue(packet)
        self.flush()

    def publish_control(self, packet):
        # Native observations/status bypass its telemetry outbox. This also lets
        # a deliberate pending-tail fixture report its real unaccepted frame.
        assert packet["type"] in {"hello", "observation", "telemetry_status"}
        self.send_frozen(json.dumps(packet).encode())

    def delivery_status(self, world):
        return {
            "version": 1,
            "type": "telemetry_status",
            "world": world,
            "bot_id": 7,
            # Capture after flushing, rather than reusing the preceding tick time.
            "captured_ms": int(time.monotonic() * 1000),
            "issued_sequence": self.issued_sequence,
            "accepted_sequence": self.accepted_sequence,
            "pending_frames": len(self.pending),
            "pending_bytes": self.pending_bytes,
            "overflow_frames": self.overflow_frames,
            "discarded_frames": self.discarded_frames,
        }


def exercise_supervised_worker(
    provider,
    reason,
    *,
    delivery_mode="healthy",
    stop_during_tail=None,
    close_fault=None,
):
    with tempfile.TemporaryDirectory(prefix="bench-stop-") as temporary:
        work = Path(temporary)
        peer = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        peer.bind(str(work / "server.sock"))
        peer.setblocking(False)
        config = {
            "provider": provider,
            "mode": "shadow" if provider == "native" else "active",
            "socket_directory": str(work),
            "state_file": str(work / "state.db"),
            "bots": [7],
            "memory_mode": "frozen",
            "run_seconds": 60 if reason == "proposal_timeout" else 10,
            "benchmark_supervision": True,
            "recording": {"path": str(work / "replay.db"), "namespace": "stops"},
        }
        path = work / "config.json"
        path.write_text(json.dumps(config))
        worker_command = [sys.executable, "-m", "canary_brain.cli"]
        if close_fault:
            assert close_fault in {"schema", "counter_regression", "budget_stop"}
            # Deterministic finalization boundary injection, not a claim about
            # Selector scheduling: apparent tail confirmation precedes close.
            shim = work / "close_fault.py"
            shim.write_text(
                textwrap.dedent(
                    f"""
                    from pathlib import Path
                    from canary_brain.recording import Recorder
                    from canary_brain.store import Store
                    from canary_brain.cli import main

                    original_close = Recorder.close

                    def close(recorder):
                        if not recorder.closed:
                            fault = {close_fault!r}
                            if fault == "budget_stop":
                                Store(Path({str(work / "state.db")!r})).put(
                                    "budget_stop", "7", {{"at": "close-injection"}}
                                )
                            else:
                                recorder.native_delivery_error(7, fault)
                            Path({str(work / "close-injected")!r}).write_text(fault)
                        original_close(recorder)

                    Recorder.close = close
                    main()
                    """
                )
            )
            worker_command = [sys.executable, str(shim)]
        with (work / "worker.log").open("w") as log:
            process = subprocess.Popen(
                [
                    *worker_command,
                    "serve",
                    "--config",
                    str(path),
                ],
                env={
                    **os.environ,
                    "PYTHONPATH": str(Path(__file__).parents[1] / "src"),
                },
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 4
                while not (work / "worker.sock").exists():
                    assert process.poll() is None, (work / "worker.log").read_text()
                    assert time.monotonic() < deadline
                    time.sleep(0.02)
                # Deliberate delay after readiness: the observed horizon starts afterward.
                if reason == "completed":
                    time.sleep(2)
                packet = observation()
                packet.update(
                    party=None, autonomous=True, mode=config["mode"], sequence=0
                )
                packet["bot"].update(
                    state="IDLE", objective_running=False, xp=98800, health=100
                )
                packet["actions"] = [
                    {
                        "id": "continue",
                        "action": "continue",
                        "description": "continue",
                        "ttl_ms": 1500,
                    }
                ]
                if reason == "proposal_timeout":
                    packet["actions"] += [
                        {
                            "id": "resupply",
                            "action": "resupply",
                            "description": "resupply",
                            "ttl_ms": 5000,
                        },
                        {
                            "id": "hunt:399",
                            "action": "hunt",
                            "description": "hunt",
                            "ttl_ms": 5000,
                        },
                    ]
                started = time.monotonic()
                publisher = SyntheticPublisher(peer, str(work / "worker.sock"))
                hello_world = None
                next_delivery = 0
                injected = False
                pending_tail = False
                frozen_status = None
                tail_stop_injected = False
                while process.poll() is None and time.monotonic() - started < (
                    36 if reason == "proposal_timeout" else 14
                ):
                    elapsed = time.monotonic() - started
                    if stop_during_tail and not tail_stop_injected and elapsed >= 9:
                        reader = ReplayReader(work / "replay.db")
                        run = reader.runs()[0]["id"]
                        waiting = any(
                            event["kind"] == "lifecycle"
                            and event["data"].get("phase")
                            == "native_telemetry_tail_wait"
                            for event in reader.all_events(run)
                        )
                        if waiting:
                            if stop_during_tail == "operator_stop":
                                process.terminate()
                            else:
                                assert stop_during_tail == "budget_stop"
                                Store(work / "state.db").put(
                                    "budget_stop", "7", {"at": time.time()}
                                )
                            tail_stop_injected = True
                    if reason == "recording_gap" and elapsed > 0.3 and not injected:
                        run = ReplayReader(work / "replay.db").runs()[0]["id"]
                        # The real writer may be committing concurrently. Retry
                        # only SQLite contention, within a bounded test window.
                        for attempt in range(20):
                            try:
                                RecordingStore(work / "replay.db").append(
                                    {
                                        "run": run,
                                        "key": "injected-gap",
                                        "segment": "test",
                                        "t_ms": 100,
                                        "wall": time.time(),
                                        "kind": "gap",
                                        "data": {"reason": "storage_limit"},
                                    }
                                )
                                break
                            except sqlite3.OperationalError as error:
                                if "locked" not in str(error) or attempt == 19:
                                    raise
                                time.sleep(0.05)
                        injected = True
                    if reason != "observation_stale" or elapsed < 0.4:
                        packet["sequence"] += 1
                        packet["captured_ms"] = int(time.monotonic() * 1000)
                        if reason == "world_changed" and elapsed > 0.3:
                            packet["world"] = "changed"
                    try:
                        if packet["world"] != hello_world:
                            publisher.publish_control(
                                {
                                    "version": 1,
                                    "type": "hello",
                                    "world": packet["world"],
                                    "capabilities": {
                                        "lifecycle_telemetry": 1,
                                        "keep_awake": True,
                                        "telemetry_delivery": 1,
                                    },
                                }
                            )
                            hello_world = packet["world"]
                        if reason != "observation_stale" or elapsed < 0.4:
                            publisher.publish_control(packet)
                        if elapsed >= next_delivery:
                            if not pending_tail:
                                telemetry = {
                                    "version": 1,
                                    "type": "telemetry",
                                    "world": packet["world"],
                                    "bot_id": 7,
                                    "captured_ms": int(time.monotonic() * 1000),
                                    "deaths": 13
                                    if reason == "deaths_limit" and elapsed > 0.3
                                    else 10,
                                    "phase": "alive",
                                    "model_owned": False,
                                }
                                if delivery_mode == "pending_tail" and elapsed >= 8:
                                    publisher.enqueue(telemetry)
                                    pending_tail = True
                                else:
                                    publisher.publish(telemetry)
                            # Match native lifecycle cadence; observations still
                            # stress fresh choices without a 20 Hz telemetry flood.
                            next_delivery = elapsed + 1
                            status = publisher.delivery_status(packet["world"])
                            if delivery_mode == "stale_status":
                                if elapsed < 8:
                                    frozen_status = status
                                else:
                                    assert frozen_status is not None
                                    status = frozen_status
                            if delivery_mode != "missing_status":
                                publisher.publish_control(status)
                    except (FileNotFoundError, ConnectionRefusedError):
                        break
                    try:
                        while peer.recv(32768):
                            pass
                    except BlockingIOError:
                        pass
                    time.sleep(0.05)
                assert process.wait(timeout=3) == 0, (work / "worker.log").read_text()
                if stop_during_tail:
                    assert tail_stop_injected, (
                        "worker never entered its public tail wait"
                    )
                with sqlite3.connect(work / "state.db") as db:
                    stopped = json.loads(
                        db.execute(
                            "SELECT data FROM records WHERE kind='run_stop' AND key='end'"
                        ).fetchone()[0]
                    )
                    assert (
                        db.execute("SELECT COUNT(*) FROM requests").fetchone()[0] == 0
                    )
                reader = ReplayReader(work / "replay.db")
                run = reader.runs()[0]["id"]
                events = list(reader.all_events(run))
                if close_fault:
                    assert (work / "close-injected").read_text() == close_fault
                    assert any(
                        event["kind"] == "lifecycle"
                        and event["data"].get("phase")
                        == "native_telemetry_tail_confirmed"
                        for event in events
                    ), "close injection must follow apparent tail confirmation"
                assert stopped["reason"] == reason, {
                    "stop": stopped,
                    "gaps": [
                        event["data"] for event in events if event["kind"] == "gap"
                    ],
                    "delivery_phases": [
                        event["data"]
                        for event in events
                        if event["kind"] == "lifecycle"
                        and event["data"]
                        .get("phase", "")
                        .startswith("native_telemetry_tail")
                    ],
                }
                if reason == "proposal_timeout":
                    assert 30 < stopped["elapsed_seconds"] <= 32.2
                assert not (work / "worker.sock").exists()
                if reason == "completed":
                    assert 10 <= stopped["elapsed_seconds"] <= 11.2
                    reader = ReplayReader(work / "replay.db")
                    run = reader.runs()[0]["id"]
                    samples = [
                        e for e in reader.all_events(run) if e["kind"] == "sample"
                    ]
                    assert (
                        9 <= (samples[-1]["t_ms"] - samples[0]["t_ms"]) / 1000 <= 11.2
                    )
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=4)
                peer.close()


@pytest.mark.parametrize("provider", ["native", "fake"])
@pytest.mark.parametrize(
    "reason",
    [
        "completed",
        "deaths_limit",
        "world_changed",
        "observation_stale",
        "recording_gap",
    ],
)
def test_supervised_worker_stops_and_closes_ipc_without_inference(provider, reason):
    exercise_supervised_worker(provider, reason)


def test_invalid_fake_choices_do_not_reset_the_real_proposal_deadline():
    exercise_supervised_worker("fake", "proposal_timeout")


def test_benchmark_does_not_complete_without_a_delivery_status():
    exercise_supervised_worker(
        "native", "native_transport_unconfirmed", delivery_mode="missing_status"
    )


@pytest.mark.parametrize("delivery_mode", ["pending_tail", "stale_status"])
def test_benchmark_does_not_complete_with_an_unconfirmed_tail(delivery_mode):
    exercise_supervised_worker(
        "native", "native_transport_unconfirmed", delivery_mode=delivery_mode
    )


@pytest.mark.parametrize("reason", ["operator_stop", "budget_stop"])
def test_external_stop_wins_while_native_tail_is_waiting(reason):
    exercise_supervised_worker(
        "native", reason, delivery_mode="missing_status", stop_during_tail=reason
    )


@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        ("schema", "native_transport_unconfirmed"),
        ("counter_regression", "native_transport_unconfirmed"),
        ("budget_stop", "budget_stop"),
    ],
)
def test_finalization_revalidates_after_apparent_tail_confirmation(fault, reason):
    exercise_supervised_worker("native", reason, close_fault=fault)


def test_synthetic_peer_retries_the_same_telemetry_frame_under_backpressure(
    monkeypatch,
):
    real_socket = socket.socket
    attempts = []

    class BackpressuredPeer:
        def __init__(self, *args, **kwargs):
            self.peer = real_socket(*args, **kwargs)

        def __getattr__(self, name):
            return getattr(self.peer, name)

        def sendto(self, data, address):
            packet = json.loads(data)
            if packet.get("type") == "telemetry" and packet["sequence"] == 2:
                attempts.append(bytes(data))
                if len(attempts) == 1:
                    raise BlockingIOError(errno.EAGAIN, "injected synthetic pressure")
            return self.peer.sendto(data, address)

    monkeypatch.setattr(socket, "socket", BackpressuredPeer)
    exercise_supervised_worker("native", "completed")
    assert len(attempts) >= 2
    assert len(set(attempts)) == 1


def test_synthetic_outbox_freezes_frames_and_preserves_fifo_across_retryable_errors():
    class Peer:
        def __init__(self):
            self.attempts = []
            self.accepted = []
            self.errors = iter((errno.EAGAIN, errno.ENOBUFS, errno.EINTR))

        def sendto(self, payload, address):
            self.attempts.append(bytes(payload))
            code = next(self.errors, None)
            if code is not None:
                raise OSError(code, "injected synthetic pressure")
            self.accepted.append(json.loads(payload))
            return len(payload)

    peer = Peer()
    publisher = SyntheticPublisher(peer, "diagnostic-worker")
    packet = {"type": "observation", "value": "original"}
    publisher.enqueue(packet)
    publisher.enqueue({"type": "telemetry"})
    packet["value"] = "changed-after-enqueue"
    before = publisher.delivery_status("world")
    assert before["issued_sequence"] == 1
    assert before["accepted_sequence"] == 0
    assert before["pending_frames"] == 2 and before["pending_bytes"] > 0
    publisher.flush()
    assert peer.accepted == [
        {"type": "observation", "value": "original"},
        {"type": "telemetry", "sequence": 1},
    ]
    assert len(set(peer.attempts[:4])) == 1
    after = publisher.delivery_status("world")
    assert after["issued_sequence"] == after["accepted_sequence"] == 1
    assert after["pending_frames"] == after["pending_bytes"] == 0
    assert after["overflow_frames"] == after["discarded_frames"] == 0
    assert after["captured_ms"] >= before["captured_ms"]


def test_synthetic_outbox_timeout_retains_the_unaccepted_sequence():
    class Peer:
        def sendto(self, *_):
            raise BlockingIOError(errno.EAGAIN, "injected permanent pressure")

    publisher = SyntheticPublisher(Peer(), "diagnostic-worker", timeout=0)
    publisher.enqueue({"type": "telemetry"})
    with pytest.raises(AssertionError, match="could not drain"):
        publisher.flush()
    status = publisher.delivery_status("world")
    assert status["issued_sequence"] == 1 and status["accepted_sequence"] == 0
    assert status["pending_frames"] == 1 and status["pending_bytes"] > 0
    assert status["discarded_frames"] == 0


def test_synthetic_pending_tail_can_report_status_without_flushing_the_frame():
    class Peer:
        def __init__(self):
            self.accepted = []

        def sendto(self, payload, _):
            self.accepted.append(json.loads(payload))
            return len(payload)

    peer = Peer()
    publisher = SyntheticPublisher(peer, "diagnostic-worker")
    publisher.enqueue({"type": "telemetry"})
    frozen_frame = publisher.pending[0]
    publisher.publish_control({"type": "observation"})
    publisher.publish_control(publisher.delivery_status("world"))
    assert [packet["type"] for packet in peer.accepted] == [
        "observation",
        "telemetry_status",
    ]
    status = peer.accepted[-1]
    assert status["issued_sequence"] == 1 and status["accepted_sequence"] == 0
    assert status["pending_frames"] == 1 and status["pending_bytes"] > 0
    assert publisher.pending[0] == frozen_frame


@pytest.mark.parametrize("limit", ["frames", "bytes"])
def test_synthetic_outbox_overflow_is_explicit_and_latched(limit):
    publisher = SyntheticPublisher(None, "diagnostic-worker")
    if limit == "frames":
        for _ in range(64):
            publisher.enqueue({"type": "telemetry"})
        packet = {"type": "telemetry"}
    else:
        packet = {"type": "telemetry", "padding": "x" * (128 * 1024)}
    with pytest.raises(AssertionError, match="bounded outbox"):
        publisher.enqueue(packet)
    status = publisher.delivery_status("world")
    assert status["overflow_frames"] == status["discarded_frames"] == 1
    assert status["issued_sequence"] == (65 if limit == "frames" else 1)
    assert status["accepted_sequence"] == 0
    assert status["pending_frames"] == (64 if limit == "frames" else 0)


@pytest.mark.parametrize("failure", ["fatal-errno", "partial"])
def test_synthetic_outbox_never_marks_a_failed_datagram_as_accepted(failure):
    class Peer:
        def sendto(self, *_):
            if failure == "fatal-errno":
                raise OSError(errno.EIO, "injected synthetic failure")
            return 0

    publisher = SyntheticPublisher(Peer(), "diagnostic-worker")
    publisher.enqueue({"type": "telemetry"})
    with pytest.raises(OSError if failure == "fatal-errno" else AssertionError):
        publisher.flush()
    status = publisher.delivery_status("world")
    assert status["pending_frames"] == 1 and status["accepted_sequence"] == 0
