"""Native delivery evidence must expose losses and certify the frozen tail."""

import asyncio
from types import SimpleNamespace

import pytest
from test_protocol import observation
from test_recording import recorder

from canary_brain.controller import Controller
from canary_brain.protocol import Observation, TelemetryStatus
from canary_brain.recording import ReplayReader
from canary_brain.store import Store


def status(**changes):
    return {
        "version": 1,
        "type": "telemetry_status",
        "world": "world-a",
        "bot_id": 7,
        "captured_ms": 2000,
        "issued_sequence": 3,
        "accepted_sequence": 3,
        "pending_frames": 0,
        "pending_bytes": 0,
        "overflow_frames": 0,
        "discarded_frames": 0,
        **changes,
    }


async def test_controller_records_native_delivery_evidence(tmp_path):
    recording = recorder(tmp_path)
    controller = Controller(
        Store(tmp_path / "synthetic.db"),
        object(),
        lambda _: None,
        roster={7},
        observe_only=True,
        recorder=recording,
    )
    try:
        await controller.handle(observation())
        await controller.handle(status())
    finally:
        await controller.close()
        recording.close()
    events = list(ReplayReader(recording.config.path).all_events("qa:7"))
    delivery = [
        event["data"]
        for event in events
        if event["data"].get("phase") == "native_telemetry_status"
    ]
    assert delivery == [
        {
            key: value
            for key, value in status().items()
            if key not in {"version", "type", "bot_id"}
        }
        | {"phase": "native_telemetry_status"}
    ]


@pytest.mark.parametrize("counter", ["overflow_frames", "discarded_frames"])
async def test_native_loss_status_marks_gap_even_without_a_later_telemetry_frame(
    tmp_path, counter
):
    recording = recorder(tmp_path)
    controller = Controller(
        Store(tmp_path / "synthetic.db"),
        object(),
        lambda _: None,
        roster={7},
        observe_only=True,
        recorder=recording,
    )
    try:
        await controller.handle(status(issued_sequence=4, **{counter: 1}))
    finally:
        await controller.close()
        recording.close()
    read = ReplayReader(recording.config.path)
    assert read.run("qa:7")["incomplete"]
    gaps = [
        event["data"] for event in read.all_events("qa:7") if event["kind"] == "gap"
    ]
    assert gaps == [
        {
            "reason": "native_telemetry_delivery_loss",
            "world": "world-a",
            "overflow_frames": int(counter == "overflow_frames"),
            "discarded_frames": int(counter == "discarded_frames"),
        }
    ]


def test_tail_requires_a_fresh_empty_producer_watermark_and_received_sequence():
    from canary_brain.benchmark_stops import TelemetryTail

    snapshot = Observation.model_validate(observation() | {"captured_ms": 2000})
    tail = TelemetryTail(snapshot, deadline=13.0)
    assert not tail.confirm(None, ("world-a", 3))
    assert not tail.confirm(
        TelemetryStatus.model_validate(status(captured_ms=1999)), ("world-a", 3)
    )
    assert not tail.confirm(TelemetryStatus.model_validate(status()), ("world-a", 2))
    assert tail.confirm(TelemetryStatus.model_validate(status()), ("world-a", 3))
    assert tail.required_sequence == 3


@pytest.mark.parametrize(
    "changes,received",
    [
        ({"issued_sequence": 0, "accepted_sequence": 0}, ("world-a", 0)),
        (
            {"issued_sequence": 4, "pending_frames": 1, "pending_bytes": 200},
            ("world-a", 3),
        ),
        ({"issued_sequence": 4, "accepted_sequence": 4}, ("world-a", 3)),
        ({"overflow_frames": 1}, ("world-a", 3)),
        ({"discarded_frames": 1}, ("world-a", 3)),
        ({"world": "replacement-world"}, ("world-a", 3)),
        ({}, ("replacement-world", 3)),
        ({}, None),
    ],
)
def test_unconfirmed_tail_never_certifies_success(changes, received):
    from canary_brain.benchmark_stops import TelemetryTail

    tail = TelemetryTail(Observation.model_validate(observation()), deadline=13)
    assert not tail.confirm(TelemetryStatus.model_validate(status(**changes)), received)


def test_first_healthy_status_fixes_cutoff_without_chasing_newer_frames():
    from canary_brain.benchmark_stops import TelemetryTail

    tail = TelemetryTail(Observation.model_validate(observation()), deadline=13)
    first = TelemetryStatus.model_validate(status())
    assert not tail.confirm(first, ("world-a", 2))
    assert tail.required_sequence == 3
    newer = TelemetryStatus.model_validate(
        status(
            captured_ms=3000,
            issued_sequence=5,
            accepted_sequence=4,
            pending_frames=1,
            pending_bytes=200,
        )
    )
    assert tail.confirm(newer, ("world-a", 4))
    assert tail.required_sequence == 3
    assert tail.cutoff == first
    assert not tail.confirm(newer, ("world-a", 4), invalid=True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("accepted_sequence", 4),
        ("pending_frames", 1),
        ("pending_bytes", 100),
        ("issued_sequence", True),
        ("overflow_frames", "0"),
    ],
)
def test_inconsistent_or_coerced_delivery_status_is_rejected(field, value):
    with pytest.raises(ValueError):
        TelemetryStatus.model_validate(status(**{field: value}))


@pytest.mark.parametrize(
    "bad",
    [
        {"issued_sequence": "3"},
        {"accepted_sequence": 4},
        {"captured_ms": 1999},
    ],
)
async def test_invalid_or_regressing_status_cannot_reuse_previous_healthy_status(
    tmp_path, bad
):
    recording = recorder(tmp_path)
    controller = Controller(
        Store(tmp_path / "synthetic.db"),
        object(),
        lambda _: None,
        roster={7},
        observe_only=True,
        recorder=recording,
    )
    try:
        await controller.handle(status())
        await controller.handle(status(**bad))
        assert 7 in recording.delivery_invalid
    finally:
        await controller.close()
        recording.close()
    assert any(
        event["data"].get("phase") == "native_telemetry_status_invalid"
        for event in ReplayReader(recording.config.path).all_events("qa:7")
    )


async def test_required_delivery_capability_blocks_old_bridge_but_legacy_is_compatible(
    tmp_path,
):
    recording = recorder(tmp_path)
    store = Store(tmp_path / "synthetic.db")
    required = Controller(
        store,
        object(),
        lambda _: None,
        roster={7},
        recorder=recording,
        observe_only=True,
        require_benchmark_bridge=True,
        require_telemetry_delivery=True,
    )
    old_hello = {
        "version": 1,
        "type": "hello",
        "world": "world-a",
        "capabilities": {"lifecycle_telemetry": 1, "keep_awake": True},
    }
    legacy = Controller(store, object(), lambda _: None, require_benchmark_bridge=True)
    try:
        await legacy.handle(old_hello)
        assert legacy.bridge_ready
        await required.handle(old_hello)
        assert not required.bridge_ready
        await required.handle(observation())
        assert not required.latest
        await required.handle(
            old_hello
            | {"capabilities": old_hello["capabilities"] | {"telemetry_delivery": 1}}
        )
        await required.handle(observation())
        assert required.bridge_ready
        await required.handle(status())
        assert (
            required.latest[7].model_dump()
            == Observation.model_validate(observation()).model_dump()
        )
    finally:
        await required.close()
        recording.close()


def test_frozen_horizon_preserves_score_and_keeps_post_horizon_diagnostics(
    tmp_path, monkeypatch
):
    import canary_brain.recording as recording_module
    from canary_brain.replay import summary

    clock = [1000.0]
    monkeypatch.setattr(recording_module.time, "monotonic", lambda: clock[0])
    recording = recorder(tmp_path)
    snapshot = Observation.model_validate(observation() | {"captured_ms": 2000})
    recording.observe(snapshot)
    recording.native_event(
        7, "world-a", 1, {"captured_ms": 1999, "phase": "alive", "deaths": 0}
    )
    clock[0] += 1800
    assert recording.freeze_horizon(snapshot)
    clock[0] += 3
    later = observation() | {"captured_ms": 5000, "sequence": 11}
    later["bot"]["xp"] = 999999
    later["bot"]["level"] = 81
    recording.observe(Observation.model_validate(later))
    recording.native_event(
        7, "world-a", 2, {"captured_ms": 5000, "phase": "dead", "deaths": 10}
    )
    recording.emit(7, "outcome", {"status": "completed", "metrics": {"xp_delta": 999}})
    recording.close()
    read = ReplayReader(recording.config.path)
    events = list(read.all_events("qa:7"))
    final = next(event for event in events if event["key"] == "horizon-final-sample")
    assert final["t_ms"] == 1800000
    assert [
        event["data"]["bot"]["xp"] for event in events if event["kind"] == "sample"
    ] == [1000, 1000]
    assert not any(event["kind"] == "outcome" for event in events)
    assert {event["data"].get("phase") for event in events} >= {
        "post_horizon_sample",
        "post_horizon_telemetry",
        "post_horizon_outcome",
    }
    assert summary(read, "qa:7")["metrics"]["xp_delta"] == 0
    assert summary(read, "qa:7")["metrics"]["deaths"] == 0
    assert not summary(read, "qa:7")["metrics"]["levels"]


def test_delayed_pre_horizon_death_still_counts_and_requests_keep_financial_terminal(
    tmp_path,
):
    from canary_brain.replay import summary

    recording = recorder(tmp_path)
    snapshot = Observation.model_validate(observation() | {"captured_ms": 2000})
    recording.observe(snapshot)
    recording.native_event(
        7, "world-a", 1, {"captured_ms": 1000, "phase": "alive", "deaths": 0}
    )
    assert recording.freeze_horizon(snapshot)
    recording.native_event(
        7, "world-a", 2, {"captured_ms": 1999, "phase": "dead", "deaths": 1}
    )
    terminal_data = {
        "request_id": "synthetic-in-flight",
        "phase": "failed",
        "unsettled": True,
        "reserved_nanousd": 123,
    }
    recording.emit(7, "request", terminal_data)
    recording.close()
    read = ReplayReader(recording.config.path)
    assert summary(read, "qa:7")["metrics"]["deaths"] == 1
    terminal = next(e for e in read.all_events("qa:7") if e["kind"] == "request")
    assert terminal["data"] == terminal_data


async def test_horizon_cancels_in_flight_request_without_releasing_unknown_charge(
    tmp_path,
):
    from test_gateway import gateway

    from canary_brain.gateway import GatewayProvider

    recording = recorder(tmp_path)
    store = Store(tmp_path / "synthetic-ledger.db")
    sdk_started = asyncio.Event()
    calls = []

    async def create(**body):
        calls.append(body)
        sdk_started.set()
        await asyncio.Event().wait()

    client = SimpleNamespace(
        responses=SimpleNamespace(with_raw_response=SimpleNamespace(create=create))
    )
    provider = GatewayProvider(store, client, gateway=gateway(), recorder=recording)
    sent = []
    controller = Controller(
        store,
        provider,
        sent.append,
        mode="active",
        roster={7},
        recorder=recording,
        memory_mode="frozen",
    )
    try:
        packet = observation()
        await controller.handle(packet)
        await asyncio.wait_for(sdk_started.wait(), 2)
        before = store.budget()["reserved"]
        assert before > 0
        assert recording.freeze_horizon(Observation.model_validate(packet))
        controller.observe_only = True
        await controller.close()
        await controller.handle(packet | {"sequence": 11, "captured_ms": 2000})
        assert not controller.pending
    finally:
        await controller.close()
        recording.close()
    events = list(ReplayReader(recording.config.path).all_events("qa:7"))
    failed = next(
        event
        for event in events
        if event["kind"] == "request" and event["data"]["phase"] == "failed"
    )
    stopped = next(
        event
        for event in events
        if event["kind"] == "segment" and event["data"]["phase"] == "stopped"
    )
    assert failed["data"]["error"] == "CancelledError"
    assert failed["data"]["unsettled"]
    assert failed["data"]["reserved_nanousd"] == before
    assert failed["id"] < stopped["id"]
    assert Store(store.path).budget()["reserved"] == before
    assert store.budget()["spent"] == 0
    assert len(calls) == 1
    assert not any(packet["type"] == "intent" for packet in sent)
