"""Shutdown races must not certify a completed or financially stopped run."""

import asyncio
import time

import pytest

from canary_brain import runtime
from canary_brain.benchmark_stops import Stops
from canary_brain.recording import RecordingStore, ReplayReader
from canary_brain.store import Store


@pytest.mark.parametrize("when", ["before_stop", "during_flush"])
async def test_gap_wins_over_completion_even_when_written_during_close(
    tmp_path, monkeypatch, when
):
    config = runtime.Configuration(
        provider="native",
        mode="shadow",
        bots=[7],
        socket_directory=tmp_path,
        state_file=tmp_path / "state.db",
        run_seconds=10,
        benchmark_supervision=True,
        native_source_revision="a" * 40,
        recording={"path": tmp_path / "replay.db", "namespace": "finalize"},
    )
    now = time.monotonic()
    monkeypatch.setattr(
        runtime, "Stops", lambda **kw: Stops(start=now - 11, last=now, **kw)
    )
    original = runtime.Recorder

    def gap(recorder):
        run = next(iter(recorder.manifests.values())).run_id
        RecordingStore(recorder.config.path).append(
            {
                "run": run,
                "key": "late-gap",
                "segment": "fixture",
                "t_ms": 10,
                "wall": time.time(),
                "kind": "gap",
                "data": {"reason": "storage_limit"},
            }
        )

    class Recorder(original):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            if when == "before_stop":
                gap(self)

        def close(self):
            super().close()
            if when == "during_flush":
                gap(self)

    monkeypatch.setattr(runtime, "Recorder", Recorder)
    await runtime.run(config, asyncio.Event())
    assert Store(config.state_file).get("run_stop", "end")["reason"] == "recording_gap"
    assert ReplayReader(config.recording.path).runs()[0]["incomplete"]


def test_completed_requires_observations_covering_the_horizon():
    stop = Stops(horizon=10, start=0, last=5.5)
    assert stop.check(10) is None
    stop.last = 10
    assert stop.check(10) == "completed"


def test_old_sequence_cannot_refresh_health_or_progress():
    from test_benchmark_stops import observation

    stop = Stops(horizon=100)
    first = observation()
    first["sequence"] = 2
    stop.observe(first, 0)
    for sequence in [2, 1]:
        old = observation(xp=999)
        old["sequence"] = sequence
        stop.observe(old, 4)
    assert stop.last == 0 and stop.progress_at == 0
    assert stop.check(5.1) == "observation_stale"
