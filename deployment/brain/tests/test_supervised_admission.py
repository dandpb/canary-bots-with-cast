"""Offline worker admission/recording counterexamples; fresh synthetic stores."""

from copy import deepcopy

import pytest
from test_protocol import observation
from test_recording import recorder

from canary_brain.benchmark_stops import Stops
from canary_brain.controller import Controller
from canary_brain.recording import ReplayReader
from canary_brain.store import Store
from canary_brain.testing import FakeProvider

SOURCE = "a" * 40
CAPS = {
    "lifecycle_telemetry": 1,
    "telemetry_delivery": 1,
    "telemetry_admission": 1,
    "telemetry_fence": 1,
    "keep_awake": True,
}


def make(tmp_path, **kwargs):
    recording = recorder(tmp_path)
    sent = []
    c = Controller(
        Store(tmp_path / "synthetic.db"),
        FakeProvider(),
        sent.append,
        roster={7},
        recorder=recording,
        benchmark_stops=Stops(horizon=10),
        native_source_revision=SOURCE,
        **kwargs,
    )
    return c, recording, sent


async def hello(c, caps=None, world="world-a"):
    await c.handle(
        {
            "version": 1,
            "type": "hello",
            "world": world,
            "capabilities": CAPS if caps is None else caps,
        }
    )


def admission(c, **changes):
    data = {
        "version": 1,
        "type": "telemetry_admitted",
        "world": "world-a",
        "bot_id": 7,
        "nonce": c.native_run.nonce,
        "begin_sequence": 220,
        "captured_ms": 1000,
        "deaths": 2,
        "observation": observation(),
        "source": SOURCE,
        "source_dirty": False,
        "fault": "",
    }
    return data | changes


def frame(c, sequence=220, **changes):
    return {
        "version": 1,
        "type": "telemetry",
        "world": "world-a",
        "bot_id": 7,
        "sequence": sequence,
        "captured_ms": 1000,
        "deaths": 2,
        "phase": "alive",
        "run_nonce": c.native_run.nonce if sequence == 220 else "",
    } | changes


def status(c, **changes):
    return {
        "version": 1,
        "type": "telemetry_status",
        "world": "world-a",
        "bot_id": 7,
        "captured_ms": 1801000,
        "issued_sequence": 220,
        "accepted_sequence": 220,
        "pending_frames": 0,
        "pending_bytes": 0,
        "overflow_frames": 0,
        "discarded_frames": 0,
        "fence_nonce": c.native_run.fence_nonce,
    } | changes


async def started(c):
    await hello(c)
    await c.handle(frame(c))  # B can arrive before a lost/retried reply
    await c.handle(admission(c))


async def finish(c, r):
    await c.close()
    r.close()


async def test_durable_admission_and_o0_precede_decisions(tmp_path):
    c, r, _sent = make(tmp_path)
    try:
        await hello(c)
        await c.handle(observation())
        assert not c.latest and not c.pending
        await c.handle(frame(c))
        await c.handle(admission(c))
        events = list(ReplayReader(r.config.path).all_events("qa:7"))
        assert any(e["key"] == "native-admission" for e in events)
        assert any(
            e["kind"] == "sample" and e["data"]["sequence"] == 10 for e in events
        )
        assert c.store.get("native_admission", "qa:7")["begin_sequence"] == 220
        assert c.benchmark_stops.deaths_base == 2
        assert c.native_run.ready
    finally:
        await finish(c, r)


async def test_missing_b_cannot_use_first_receipt_and_retry_keeps_boundary(tmp_path):
    c, r, _ = make(tmp_path)
    try:
        await hello(c)
        reply = admission(c)
        await c.handle(reply)
        await c.handle(deepcopy(reply))
        assert not c.native_run.ready and not c.pending
        await c.handle(frame(c, 221))
        assert c.native_run.failure == "telemetry_gap"
        assert r.native[7] == ("world-a", 219)
    finally:
        await finish(c, r)


@pytest.mark.parametrize("caps", [{}, CAPS | {"telemetry_admission": 0}])
async def test_old_peer_never_opens_decisions(tmp_path, caps):
    c, r, _ = make(tmp_path)
    try:
        await hello(c, caps)
        await c.handle(observation())
        assert c.native_run.failure and not c.pending and not c.latest
    finally:
        await finish(c, r)


async def test_native_time_first_cutoff_blocks_reflection_and_latest_inflation(
    tmp_path,
):
    c, r, _ = make(tmp_path)
    try:
        await started(c)
        short = observation() | {"sequence": 11, "captured_ms": 1799999}
        await c.handle(short)
        assert c.native_run.horizon is None
        first = observation() | {"sequence": 12, "captured_ms": 1801000}
        await c.handle(first)
        late = deepcopy(first)
        late.update(sequence=13, captured_ms=1802000)
        late["bot"]["xp"] = 999999
        await c.handle(late)
        assert c.native_run.horizon.sequence == 12
        assert r.horizons[7].bot.xp == 1000
        assert c.model_admission_closed
        c._spawn(7, "reflection", lambda: pytest.fail("late model admission"))
        assert not any(kind == "reflection" for _, kind in c.pending)
        assert c._apply(c.latest[7], "resupply") is None
        # Periodic status cannot stand in for an explicit terminal reply.
        await c.handle(status(c, fence_nonce=""))
        assert not c.native_run.confirmed
        await c.handle(status(c))
        assert c.native_run.confirmed
        r.flush()
        assert c.native_run.durable_complete()
    finally:
        await finish(c, r)


@pytest.mark.parametrize("packet", ["status", "hello", "removed", "duplicate"])
async def test_faults_stick_across_later_valid_packets(tmp_path, packet):
    c, r, _ = make(tmp_path)
    try:
        await started(c)
        if packet == "status":
            await c.handle(status(c, world="new-world"))
        elif packet == "hello":
            await hello(c, world="new-world")
        elif packet == "removed":
            await c.handle(frame(c, 221, phase="unavailable"))
        else:
            bad = observation()
            bad["captured_ms"] = 999
            await c.handle(bad)
        await c.handle(observation() | {"sequence": 100, "captured_ms": 1801000})
        await c.handle(status(c))
        assert c.native_run.failure and not c.native_run.confirmed
    finally:
        await finish(c, r)


async def test_durable_coverage_cannot_be_replaced_by_memory_watermark(tmp_path):
    c, r, _ = make(tmp_path)
    try:
        await started(c)
        await c.handle(observation() | {"sequence": 12, "captured_ms": 1801000})
        await c.handle(status(c))
        r.flush()
        assert c.native_run.durable_complete()
        with r.store.connect() as db:
            db.execute(
                "DELETE FROM replay_events WHERE event_key='native:world-a:7:220'"
            )
        assert not c.native_run.durable_complete()
    finally:
        await finish(c, r)


async def test_reply_without_b_does_not_disable_startup_watchdog(tmp_path):
    c, r, _ = make(tmp_path)
    try:
        await hello(c)
        await c.handle(admission(c))
        assert c.benchmark_stops.start is None
        assert c.store.get("run_clock", "start") is None
        assert c.model_admission_closed
    finally:
        await finish(c, r)


async def test_post_cutoff_death_is_diagnostic_but_delayed_window_death_counts(
    tmp_path,
):
    c, r, _ = make(tmp_path)
    try:
        await started(c)
        await c.handle(observation() | {"sequence": 12, "captured_ms": 1801000})
        await c.handle(frame(c, 221, captured_ms=1801000, deaths=3, phase="dead"))
        assert c.benchmark_stops.deaths == 1
        await c.handle(frame(c, 222, captured_ms=1802000, deaths=5, phase="dead"))
        assert c.benchmark_stops.deaths == 1
    finally:
        await finish(c, r)


async def test_model_cancelled_before_first_execution_is_reaped(tmp_path):
    c, r, _ = make(tmp_path)
    try:
        await started(c)
        await c.close()
        assert not c.pending
    finally:
        await finish(c, r)


async def test_fence_after_deadline_cannot_restore_completion(tmp_path):
    c, r, _ = make(tmp_path)
    try:
        await started(c)
        await c.handle(observation() | {"sequence": 12, "captured_ms": 1801000})
        c.native_run.deadline = 0
        await c.handle(status(c))
        assert c.native_run.failure == "native_transport_unconfirmed"
        assert not c.native_run.confirmed
    finally:
        await finish(c, r)


async def test_committed_native_payload_must_match_validated_frame(tmp_path):
    import json

    c, r, _ = make(tmp_path)
    try:
        await started(c)
        await c.handle(observation() | {"sequence": 12, "captured_ms": 1801000})
        await c.handle(status(c))
        r.flush()
        assert c.native_run.durable_complete()
        with r.store.connect() as db:
            data = json.loads(
                db.execute(
                    "SELECT data FROM replay_events WHERE event_key='native:world-a:7:220'"
                ).fetchone()[0]
            )
            data["run_nonce"] = "different"
            db.execute(
                "UPDATE replay_events SET data=? WHERE event_key='native:world-a:7:220'",
                (json.dumps(data),),
            )
        assert not c.native_run.durable_complete()
    finally:
        await finish(c, r)


async def test_real_peer_rebind_invalidates_pinned_socket(tmp_path):
    import os
    import socket

    descriptor = os.open(tmp_path, os.O_DIRECTORY | os.O_RDONLY)
    path = f"/proc/self/fd/{descriptor}/native.sock"
    c, r, _ = make(tmp_path)
    peer = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    replacement = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        peer.bind(path)
        assert c.native_run.check_peer(path)
        os.unlink(path)
        replacement.bind(path)
        assert not c.native_run.check_peer(path)
        assert c.native_run.failure == "native_peer_changed"
    finally:
        peer.close()
        replacement.close()
        os.close(descriptor)
        await finish(c, r)


def test_worker_receipt_ttl_cannot_substitute_for_native_capture():
    stops = Stops(horizon=10, native_start_ms=1000)
    first = observation()
    stops.observe(first, 0)
    delayed = deepcopy(first)
    delayed.update(sequence=11, captured_ms=1800999)
    delayed["bot"]["xp"] += 1
    stops.observe(delayed, 1801)
    assert stops.check(1801) is None
    delayed.update(sequence=12, captured_ms=1801000)
    stops.observe(delayed, 1801.1)
    assert stops.check(1801.1) == "completed"


async def test_admission_commit_failure_cannot_release_models(tmp_path, monkeypatch):
    c, r, _ = make(tmp_path)
    try:

        def broken(_):
            raise ValueError("injected synthetic storage failure")

        monkeypatch.setattr(r, "admit_native", broken)
        await hello(c)
        await c.handle(frame(c))
        await c.handle(admission(c))
        assert c.native_run.failure == "native_admission_invalid"
        assert c.model_admission_closed and not c.latest and not c.pending
    finally:
        await finish(c, r)


async def test_ingress_capacity_rejection_is_visible_not_a_silent_drop(tmp_path):
    import asyncio
    import json
    import os
    import socket

    from canary_brain.runtime import DatagramProtocol

    c, r, _ = make(tmp_path)
    descriptor = os.open(tmp_path, os.O_DIRECTORY | os.O_RDONLY)
    path = f"/proc/self/fd/{descriptor}/native.sock"
    peer = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        peer.bind(path)
        protocol = DatagramProtocol(c, path)
        data = json.dumps(
            {"version": 1, "type": "hello", "world": "world-a", "capabilities": CAPS}
        ).encode()
        for _ in range(33):
            protocol.datagram_received(data, path)
        await asyncio.gather(*protocol.tasks)
        assert c.native_run.failure == "worker_ingress_overflow"
        assert not c.pending
    finally:
        peer.close()
        os.close(descriptor)
        await finish(c, r)
