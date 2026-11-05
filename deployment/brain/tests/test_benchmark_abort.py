import asyncio
import json
import time

import pytest
from test_benchmark import experiment

from canary_brain import benchmark
from canary_brain.benchmark import Participant
from canary_brain.recording import ReplayReader
from canary_brain.store import Store


@pytest.mark.parametrize(
    "reason",
    [
        "operator_stop",
        "world_changed",
        "observation_stale",
        "recording_gap",
        "recorder_error",
        "startup_timeout",
    ],
)
async def test_critical_stop_never_starts_the_next_paid_or_native_attempt(
    tmp_path, monkeypatch, reason
):
    config = experiment(tmp_path)
    config.participants.append(Participant(name="second", kind="native"))
    started = []

    class Harness(benchmark.DockerFixture):
        def start_database(self):
            started.append(self.directory.name)

        def character(self):
            return json.loads((config.fixture / "character.json").read_text())

        def start_game(self):
            pass

        def close(self):
            pass

    async def worker(configuration, stopped):
        (configuration.socket_directory / "worker.sock").touch()
        state = Store(configuration.state_file)
        state.put("run_clock", "start", {"monotonic": time.monotonic()})
        state.put("run_stop", "end", {"reason": reason})

    monkeypatch.setattr(benchmark, "DockerFixture", Harness)
    monkeypatch.setattr(benchmark, "run", worker)
    expected = asyncio.CancelledError if reason == "operator_stop" else RuntimeError
    with pytest.raises(expected):
        await benchmark.run_campaign(config, live=True)
    assert started == ["native-0"]
    reader = ReplayReader(config.output / "recording.sqlite3")
    assert reader.run("qa:native:0")["status"] == (
        "interrupted" if reason == "operator_stop" else "failed"
    )
    assert len(reader.runs()) == 1
