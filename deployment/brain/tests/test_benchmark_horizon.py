"""A delayed first observation must not shorten an independent run."""

import asyncio
import json
import time
from types import SimpleNamespace

import pytest
from test_benchmark import experiment

from canary_brain import benchmark
from canary_brain.store import Store


@pytest.mark.asyncio
@pytest.mark.parametrize("premature", [False, True])
async def test_runner_waits_for_the_workers_observed_horizon(
    tmp_path, monkeypatch, premature
):
    config = experiment(tmp_path)
    clock = [0.0]
    elapsed = []
    original_sleep = asyncio.sleep

    async def advance(seconds):
        clock[0] += seconds
        await original_sleep(0)

    class Harness(benchmark.DockerFixture):
        def start_database(self):
            pass

        def character(self):
            return json.loads((config.fixture / "character.json").read_text())

        def start_game(self):
            pass

        def stop_game(self):
            pass

        def close(self):
            pass

    async def worker(configuration, stopped):
        (configuration.socket_directory / "worker.sock").touch()
        state = Store(configuration.state_file)
        # The service is healthy before the roster's first observation arrives.
        while clock[0] < 2 and not stopped.is_set():
            await original_sleep(0)
        started = clock[0]
        state.put("run_clock", "start", {"monotonic": started})
        state.put("status", str(config.bot_id), {"last_observation": time.time()})
        while (
            not stopped.is_set()
            and clock[0] - started < config.seconds
            and not premature
        ):
            await original_sleep(0)
        elapsed.append(clock[0] - started)
        if premature or elapsed[-1] >= config.seconds:
            state.put(
                "run_stop",
                "end",
                {"reason": "completed", "elapsed_seconds": elapsed[-1]},
            )

    monkeypatch.setattr(benchmark, "DockerFixture", Harness)
    monkeypatch.setattr(benchmark, "run", worker)
    monkeypatch.setattr(
        benchmark, "time", SimpleNamespace(monotonic=lambda: clock[0], time=time.time)
    )
    monkeypatch.setattr(
        benchmark,
        "asyncio",
        SimpleNamespace(
            create_task=asyncio.create_task,
            sleep=advance,
            to_thread=asyncio.to_thread,
            Event=asyncio.Event,
            gather=asyncio.gather,
            CancelledError=asyncio.CancelledError,
        ),
    )
    if premature:
        with pytest.raises(RuntimeError, match="observed horizon"):
            await benchmark.run_campaign(config, live=True)
    else:
        await benchmark.run_campaign(config, live=True)
        assert config.seconds <= elapsed[0] <= config.seconds + 1, elapsed
