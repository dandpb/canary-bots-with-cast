"""Synthetic qualification contract; no runtime, recorder or QA helper imports."""

from copy import deepcopy

import pytest
from test_protocol import observation

from canary_brain.native_admission import Admission, Qualification


def reply(**changes):
    initial = observation()
    initial["captured_ms"] = 1000
    return dict(
        version=1,
        type="telemetry_admitted",
        world="world-a",
        bot_id=7,
        nonce="attempt-a",
        begin_sequence=220,
        captured_ms=1000,
        deaths=2,
        observation=initial,
        source="a" * 40,
        source_dirty=False,
        fault="",
        **changes,
    )


def qualify():
    return Qualification(
        Admission.model_validate(reply()),
        nonce="attempt-a",
        world="world-a",
        bot_id=7,
        source="a" * 40,
    )


def frame(sequence=220, **changes):
    return dict(
        version=1,
        type="telemetry",
        world="world-a",
        bot_id=7,
        sequence=sequence,
        captured_ms=1000,
        deaths=2,
        phase="alive",
        model_owned=False,
        run_nonce="attempt-a" if sequence == 220 else "",
        **changes,
    )


def watermark(sequence=221):
    return {
        "version": 1,
        "type": "telemetry_status",
        "world": "world-a",
        "bot_id": 7,
        "captured_ms": 1801000,
        "issued_sequence": sequence,
        "accepted_sequence": sequence,
        "pending_frames": 0,
        "pending_bytes": 0,
        "overflow_frames": 0,
        "discarded_frames": 0,
    }


def horizon(q, captured=1801000, sequence=9000):
    packet = observation()
    packet.update(captured_ms=captured, sequence=sequence)
    q.observe(packet)


def test_dropped_first_frame_cannot_use_first_receipt_as_baseline():
    q = qualify()
    q.telemetry(frame(221))
    horizon(q)
    assert not q.complete(watermark())
    assert q.failure == "telemetry_gap"


def test_lost_reply_retry_and_duplicate_boundary_are_idempotent():
    q = qualify()
    q.telemetry(frame())
    q.retry(Admission.model_validate(reply()))
    q.telemetry(frame())
    q.telemetry(frame(221))
    horizon(q)
    assert q.complete(watermark())
    assert q.deaths == 0


def test_delayed_native_capture_never_uses_worker_receipt_clock():
    q = qualify()
    q.telemetry(frame())
    horizon(q, captured=1800999)
    assert not q.complete(watermark(220))
    horizon(q, sequence=9001)
    assert q.complete(watermark(220))


@pytest.mark.parametrize(
    "field,value",
    [("nonce", "wrong"), ("world", "wrong"), ("bot_id", 8), ("source", "b" * 40)],
)
def test_admission_must_match_prospective_identity(field, value):
    kwargs = {"nonce": "attempt-a", "world": "world-a", "bot_id": 7, "source": "a" * 40}
    kwargs[field] = value
    with pytest.raises(ValueError):
        Qualification(Admission.model_validate(reply()), **kwargs)


def test_death_while_reply_pending_counts_from_native_cut():
    q = qualify()
    q.telemetry(frame())
    death = frame(221)
    death.update(deaths=3, phase="dead", captured_ms=1100)
    q.telemetry(death)
    assert q.deaths == 1
    q.retry(Admission.model_validate(reply()))
    assert q.deaths == 1


@pytest.mark.parametrize(
    "field,value", [("world", "reloaded"), ("bot_id", 8), ("run_nonce", "wrong")]
)
def test_wrong_boundary_event_is_sticky(field, value):
    q = qualify()
    bad = frame()
    bad[field] = value
    q.telemetry(bad)
    q.telemetry(frame())
    horizon(q)
    assert not q.complete(watermark(220))


def test_process_crash_has_no_terminal_watermark_and_cannot_resume():
    q = qualify()
    q.telemetry(frame())
    horizon(q)
    assert not q.complete(None)
    q.abort("process_crash")
    assert not q.complete(watermark(220))
    fresh = qualify()
    assert not fresh.complete(watermark(220))


def test_changed_duplicate_reply_or_event_fails():
    q = qualify()
    q.telemetry(frame())
    changed = deepcopy(reply())
    changed["deaths"] = 3
    q.retry(Admission.model_validate(changed))
    assert q.failure == "admission_changed"
    q = qualify()
    q.telemetry(frame())
    changed_frame = frame()
    changed_frame["deaths"] = 4
    q.telemetry(changed_frame)
    assert q.failure == "telemetry_changed"


@pytest.mark.parametrize(
    "field,value",
    [
        ("pending_frames", 1),
        ("overflow_frames", 1),
        ("discarded_frames", 1),
        ("world", "new"),
    ],
)
def test_terminal_loss_or_wrong_world_fails(field, value):
    q = qualify()
    q.telemetry(frame())
    horizon(q)
    status = watermark(220)
    status[field] = value
    assert not q.complete(status)


def test_native_process_killed_after_reply_has_no_terminal_certificate():
    import json
    import subprocess
    import sys

    child = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import os,signal,sys; print(sys.argv[1],flush=True); "
                "os.kill(os.getpid(),signal.SIGKILL)"
            ),
            json.dumps(reply()),
        ],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert child.returncode == -9
    q = Qualification(
        Admission.model_validate_json(child.stdout),
        nonce="attempt-a",
        world="world-a",
        bot_id=7,
        source="a" * 40,
    )
    q.telemetry(frame())
    horizon(q)
    assert not q.complete(None)
    q.abort("process_crash")
    assert not q.complete(watermark(220))


@pytest.mark.parametrize("dirty,fault", [(True, ""), (False, "telemetry_loss")])
def test_dirty_source_or_native_fault_cannot_open_qualification(dirty, fault):
    data = reply()
    data.update(source_dirty=dirty, fault=fault)
    with pytest.raises(ValueError):
        Qualification(
            Admission.model_validate(data),
            nonce="attempt-a",
            world="world-a",
            bot_id=7,
            source="a" * 40,
        )


def test_native_time_and_death_counters_cannot_regress():
    for field, value in [("captured_ms", 999), ("deaths", 1)]:
        q = qualify()
        q.telemetry(frame())
        bad = frame(221)
        bad[field] = value
        q.telemetry(bad)
        assert q.failure == "native_regression"


def test_terminal_watermark_cannot_replace_a_missing_last_frame():
    q = qualify()
    q.telemetry(frame())
    horizon(q)
    assert not q.complete(watermark(221))
    q.telemetry(frame(221))
    assert q.complete(watermark(221))


def test_status_native_time_alone_cannot_create_horizon():
    q = qualify()
    q.telemetry(frame())
    assert not q.complete(watermark(220))


@pytest.mark.parametrize("field,value", [("captured_ms", 1001), ("world", "new")])
def test_admission_observation_must_match_cut(field, value):
    data = reply()
    data["observation"][field] = value
    with pytest.raises(ValueError):
        Admission.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("world", "reloaded"),
        ("bot_id", 8),
        ("overflow_frames", 1),
        ("discarded_frames", 1),
        ("accepted_sequence", 999),
    ],
)
def test_pre_horizon_watermark_fault_cannot_be_forgotten(field, value):
    q = qualify()
    q.telemetry(frame())
    bad = watermark(220)
    bad[field] = value
    assert not q.complete(bad)
    assert q.failure is not None
    horizon(q)
    assert not q.complete(watermark(220))


@pytest.mark.parametrize("which", ["baseline", "latest", "older"])
def test_conflicting_observation_retransmission_is_sticky(which):
    q = qualify()
    q.telemetry(frame())
    baseline = reply()["observation"]
    latest = deepcopy(baseline)
    latest.update(sequence=baseline["sequence"] + 1, captured_ms=1100)
    if which != "baseline":
        q.observe(latest)
    if which == "older":
        newer = deepcopy(latest)
        newer.update(sequence=latest["sequence"] + 1, captured_ms=1200)
        q.observe(newer)
    bad = deepcopy(baseline if which == "baseline" else latest)
    bad["captured_ms"] = 999
    q.observe(bad)
    assert q.failure == "observation_changed"
    horizon(q)
    assert not q.complete(watermark(220))


def test_exact_old_observation_retransmissions_remain_idempotent():
    q = qualify()
    q.telemetry(frame())
    baseline = reply()["observation"]
    later = deepcopy(baseline)
    later.update(sequence=baseline["sequence"] + 1, captured_ms=1100)
    q.observe(later)
    q.observe(baseline)
    q.observe(later)
    horizon(q)
    assert q.complete(watermark(220))
