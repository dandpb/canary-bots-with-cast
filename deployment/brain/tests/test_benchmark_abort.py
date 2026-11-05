import asyncio
import json
import os
import signal
import time

import pytest
from test_benchmark import experiment
from test_protocol import observation

from canary_brain import benchmark
from canary_brain.benchmark import Participant
from canary_brain.recording import RecordingStore, ReplayReader
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
        "unexpected_stop",
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


@pytest.mark.parametrize("fault", ["late_gap", "late_budget", "signal_between_trials"])
async def test_final_durable_state_and_campaign_signal_win(
    tmp_path, monkeypatch, fault
):
    config = experiment(tmp_path)
    config.participants.append(Participant(name="second", kind="native"))
    workers = []

    class Harness(benchmark.DockerFixture):
        def start_database(self):
            if fault == "signal_between_trials" and self.directory.name == "second-0":
                os.kill(os.getpid(), signal.SIGINT)

        def character(self):
            return json.loads((config.fixture / "character.json").read_text())

        def start_game(self):
            pass

        def stop_game(self):
            pass

        def close(self):
            pass

    async def worker(configuration, stopped):
        workers.append(configuration.state_file.parent.name)
        (configuration.socket_directory / "worker.sock").touch()
        state = Store(configuration.state_file)
        state.put("run_clock", "start", {"monotonic": time.monotonic() - 11})
        state.put(
            "run_stop",
            "end",
            {"reason": "completed", "elapsed_seconds": 11, "observed_seconds": 11},
        )
        identity = configuration.recording.manifests[0].run_id
        for index in [0, 1]:
            RecordingStore(configuration.recording.path).append(
                {
                    "run": identity,
                    "key": str(index),
                    "segment": "fixture",
                    "t_ms": index * 11000,
                    "wall": time.time(),
                    "kind": "sample",
                    "data": observation(),
                }
            )
        if fault == "late_gap":
            RecordingStore(configuration.recording.path).append(
                {
                    "run": identity,
                    "key": "flush-gap",
                    "segment": "fixture",
                    "t_ms": 11001,
                    "wall": time.time(),
                    "kind": "gap",
                    "data": {"reason": "storage_limit"},
                }
            )
        if fault == "late_budget":
            state.put("budget_stop", str(config.bot_id), {"at": time.time()})

    monkeypatch.setattr(benchmark, "DockerFixture", Harness)
    monkeypatch.setattr(benchmark, "run", worker)
    if fault == "late_budget":
        await benchmark.run_campaign(config, live=True)
        assert all(
            r["status"] == "budget_stop"
            for r in ReplayReader(config.output / "recording.sqlite3").runs()
        )
    else:
        expected = (
            asyncio.CancelledError if fault == "signal_between_trials" else RuntimeError
        )
        with pytest.raises(expected):
            await benchmark.run_campaign(config, live=True)
        assert workers == ["native-0"]
