"""Harness + actual runtime, SQLite and AF_UNIX; synthetic peer, no game/models."""

import asyncio
import fcntl
import json
import os
import signal
import socket
import threading
from copy import deepcopy
from pathlib import Path

import m5_qa as qa
import m5_worker as harness
import pytest
from canary_brain import runtime
from canary_brain.protocol import Observation
from canary_brain.recording import Recorder, ReplayReader
from canary_brain.store import Store
from canary_brain.supervised_native import SupervisedNative

SOURCE = "c8b3878d3e576ff8ef1561cbb2614cb77532a349"
CAPS = {
    "lifecycle_telemetry": 1,
    "telemetry_delivery": 1,
    "telemetry_admission": 1,
    "telemetry_fence": 1,
    "keep_awake": True,
}


def observation(mode):
    return {
        "version": 1,
        "type": "observation",
        "world": "qa-world",
        "sequence": 10,
        "captured_ms": 1000,
        "lease": "private-test-lease",
        "objective_generation": 2,
        "mode": mode,
        "autonomous": True,
        "bot": {
            "id": 65001,
            "name": "QA",
            "level": 20,
            "vocation": 4,
            "state": "HUNTING",
            "position": [100, 100, 7],
            "health": 100,
            "mana": 100,
            "potions": 40,
            "xp": 1000,
            "alive": True,
        },
        "party": {"leader_id": 9, "members": [9, 65001]},
        "actions": [
            {
                "id": "continue",
                "action": "continue",
                "description": "Continue",
                "ttl_ms": 1500,
            },
            {
                "id": "resupply",
                "action": "resupply",
                "description": "Resupply",
                "ttl_ms": 5000,
            },
        ],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider,fault",
    [
        (provider, fault)
        for provider in ("native", "fake")
        for fault in (
            "none",
            "drop_b",
            "gap",
            "wrong_fence",
            "peer_replaced",
            "close_false",
        )
    ]
    + [("fake", "solo_fake")],
)
async def test_combined_harness_real_admission_seal_close_and_cleanup(
    tmp_path, monkeypatch, provider, fault
):
    work = tmp_path / "attempt"
    work.mkdir(mode=0o700)
    ipc = work / "socket"
    ipc.mkdir(mode=0o700)
    descriptor = os.open(work, os.O_RDONLY | os.O_DIRECTORY)
    # Only a procfs pathname alias is short. The actual sockets/DBs remain in TMPDIR.
    directory = Path(f"/proc/self/fd/{descriptor}/socket")
    peer = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    peer.setblocking(False)
    peer.bind(str(directory / "server.sock"))
    monkeypatch.setenv("CANARY_M5_PRIVATE_ROOT", str(tmp_path))
    monkeypatch.setattr(qa, "WORK", tmp_path)
    config = qa.worker_configuration(
        work,
        provider,
        {
            "source_revision": "d" * 40,
            "native_source_revision": SOURCE,
            "fixture_sha256": "a" * 64,
            "image_id": "sha256:" + "b" * 64,
            "overrides": {},
            "harness_sha256": {},
        },
    )
    config["socket_directory"] = str(directory)
    (work / "worker.json").write_text(json.dumps(config))
    identity = config["recording"]["manifests"][0]["run_id"]
    state_path, replay_path = work / "worker.sqlite3", work / "recording.sqlite3"
    loop = asyncio.get_running_loop()
    ready = asyncio.Event()
    original_endpoint = loop.create_datagram_endpoint

    async def endpoint(*args, **kwargs):
        result = await original_endpoint(*args, **kwargs)
        ready.set()
        return result

    monkeypatch.setattr(loop, "create_datagram_endpoint", endpoint)
    close_checks, proofs = [], []
    model_proposed = asyncio.Event()
    original_record = runtime.Controller.record

    def record(controller, bot, kind, data, key=None):
        original_record(controller, bot, kind, data, key)
        if kind == "decision" and data.get("phase") == "model_proposed":
            model_proposed.set()

    monkeypatch.setattr(runtime.Controller, "record", record)
    original_close = Recorder.close
    original_proof = SupervisedNative.durable_complete

    def close(recorder):
        ending = Store(state_path).get("run_stop", "end")
        close_checks.append(ending["reason"])
        assert ending["reason"] != "completed"
        result = original_close(recorder)
        return False if fault == "close_false" else result

    def proof(native):
        result = original_proof(native)
        proofs.append(result)
        return result

    monkeypatch.setattr(Recorder, "close", close)
    monkeypatch.setattr(SupervisedNative, "durable_complete", proof)
    previous_handlers = {
        s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)
    }
    initial_tasks = asyncio.all_tasks()
    worker = asyncio.create_task(harness.run_worker(work, provider))
    received = []

    async def send(packet):
        await loop.sock_sendto(
            peer, json.dumps(packet).encode(), str(directory / "worker.sock")
        )

    async def receive(kind):
        async with asyncio.timeout(5):
            while True:
                packet = json.loads(await loop.sock_recv(peer, 32768))
                received.append(packet)
                if packet["type"] == kind:
                    return packet

    try:
        await asyncio.wait_for(ready.wait(), 5)
        await send(
            {"version": 1, "type": "hello", "world": "qa-world", "capabilities": CAPS}
        )
        request = await receive("telemetry_admit")
        initial = observation(config["mode"])
        if fault == "solo_fake":
            initial.pop("party")
        boundary = {
            "version": 1,
            "type": "telemetry",
            "world": "qa-world",
            "bot_id": 65001,
            "sequence": 220,
            "captured_ms": 1000,
            "deaths": 2,
            "phase": "alive",
            "run_nonce": request["nonce"],
        }
        if fault != "drop_b":
            await send(boundary)
        await send(
            {
                "version": 1,
                "type": "telemetry_admitted",
                "world": "qa-world",
                "bot_id": 65001,
                "nonce": request["nonce"],
                "begin_sequence": 220,
                "captured_ms": 1000,
                "deaths": 2,
                "observation": initial,
                "source": SOURCE,
                "source_dirty": False,
                "fault": "",
            }
        )
        if provider == "fake" and fault != "drop_b":
            await asyncio.wait_for(model_proposed.wait(), 5)
            admitted = Store(state_path).get("native_admission", identity)
            assert admitted["begin_sequence"] == 220  # committed before fake admission
        await send(
            boundary
            | {
                "sequence": 222 if fault == "gap" else 221,
                "run_nonce": "",
                "captured_ms": 1100,
            }
        )
        cutoff = deepcopy(initial)
        cutoff.update(sequence=11, captured_ms=1801000)
        cutoff["bot"]["xp"] = 1100
        await send(cutoff)
        later = deepcopy(cutoff)
        later.update(sequence=12, captured_ms=1802000)
        later["bot"].update(xp=9999, level=21)
        await send(later)
        if fault not in {"drop_b", "gap"}:
            fence = await receive("telemetry_fence")
            assert fence["nonce"] != request["nonce"]
            if fault == "peer_replaced":
                peer.close()
                (ipc / "server.sock").rename(ipc / "retired.sock")
                peer = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
                peer.setblocking(False)
                peer.bind(str(directory / "server.sock"))
            await send(
                {
                    "version": 1,
                    "type": "telemetry_status",
                    "world": "qa-world",
                    "bot_id": 65001,
                    "captured_ms": 1802000,
                    "issued_sequence": 221,
                    "accepted_sequence": 221,
                    "pending_frames": 0,
                    "pending_bytes": 0,
                    "overflow_frames": 0,
                    "discarded_frames": 0,
                    "fence_nonce": "wrong-fence"
                    if fault == "wrong_fence"
                    else fence["nonce"],
                    "fault": "",
                }
            )
        if fault in {"none", "solo_fake"}:
            await asyncio.wait_for(worker, 8)
        else:
            with pytest.raises(RuntimeError, match="did not complete"):
                await asyncio.wait_for(worker, 8)
        ending = Store(state_path).get("run_stop", "end")
        exported = json.loads((work / "stop.json").read_text())
        assert ending == exported
        reader = ReplayReader(replay_path)
        events = list(reader.all_events(identity))
        qualified = [e for e in events if e["key"] == "supervisor-native-qualified"]
        if fault in {"none", "solo_fake"}:
            assert (
                ending["reason"] == "completed" and ending["observed_seconds"] == 1800
            )
            admission = Store(state_path).get("native_admission", identity)
            assert (
                admission["begin_sequence"],
                admission["captured_ms"],
                admission["deaths"],
            ) == (220, 1000, 2)
            assert (
                admission["observation"]
                == Observation.model_validate(initial).model_dump()
            )
            assert admission["source"] == SOURCE and not admission["source_dirty"]
            native_keys = [e["key"] for e in events if e["key"].startswith("native:")]
            assert native_keys == [
                "native:qa-world:65001:220",
                "native:qa-world:65001:221",
            ]
            assert any(e["key"] == "native-admission" for e in events)
            scored = next(e for e in events if e["key"] == "horizon-final-sample")
            assert scored["data"]["bot"]["xp"] == 1100
            assert scored["data"]["bot"]["level"] == 20
            assert any(e["key"] == "native-terminal-fence" for e in events)
            assert len(qualified) == 1 and qualified[0]["data"]["after_flush"] is True
            assert close_checks == ["native_finalizing"] and proofs == [True]
            assert not reader.run(identity)["incomplete"]
            # Captured-time jump tests admission, not 30 real QA minutes.
            assert scored["t_ms"] - events[0]["t_ms"] < 1800000
        else:
            assert ending["reason"] != "completed" and not qualified
        with Store(state_path).connection() as db:
            assert db.execute("SELECT COUNT(*) FROM requests").fetchone()[0] == 0
        if provider == "fake" and fault in {"none", "solo_fake"}:
            decisions = [e["data"] for e in events if e["kind"] == "decision"]
            assert any(d.get("candidate") == "continue" for d in decisions)
            assert not any(e["kind"] == "intent" for e in events)
            assert any(d.get("phase") == "selected" for d in decisions) == (
                fault != "solo_fake"
            )
        if provider == "native":
            assert not [p for p in received if p["type"] == "intent"]
        assert not (ipc / "worker.sock").exists()
        lock_fd = os.open(ipc / "worker.lock", os.O_RDWR)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(lock_fd)
        assert not [t for t in threading.enumerate() if t.name == "brain-recorder"]
        assert not (asyncio.all_tasks() - initial_tasks)
        assert {s: signal.getsignal(s) for s in previous_handlers} == previous_handlers
    finally:
        if not worker.done():
            worker.cancel()
        await asyncio.gather(worker, return_exceptions=True)
        peer.close()
        (ipc / "server.sock").unlink(missing_ok=True)
        (ipc / "retired.sock").unlink(missing_ok=True)
        os.close(descriptor)
    assert not list(ipc.glob("*.sock"))
    assert state_path.exists() and replay_path.exists()  # retain every attempt
