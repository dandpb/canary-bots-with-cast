"""An operator stop must reach workers while startup waits for blocking IO."""

import asyncio
import json
import os
import signal
import threading
import time

import pytest
from test_benchmark import experiment

from canary_brain import benchmark, runtime
from canary_brain.benchmark_stops import Stops
from canary_brain.store import Store


@pytest.mark.parametrize("stage", ["character", "socket", "start_game"])
@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
async def test_signal_stops_startup_worker_before_healthcheck_returns(
    tmp_path, monkeypatch, stage, sig
):
    config = experiment(tmp_path)
    workers = []
    closed = []
    worker_stopped = threading.Event()
    startup_saw_stop = []

    class Harness(benchmark.DockerFixture):
        def start_database(self):
            pass

        def character(self):
            if stage == "character":
                os.kill(os.getpid(), sig)
                time.sleep(0.05)
            return json.loads((config.fixture / "character.json").read_text())

        def start_game(self):
            if stage == "start_game":
                os.kill(os.getpid(), sig)
                # Shutdown may exceed 300 ms on a loaded CI host.\n                startup_saw_stop.append(worker_stopped.wait(5))

        def close(self):
            closed.append(True)

    async def worker(configuration, stopped):
        workers.append(True)
        if stage == "socket":
            os.kill(os.getpid(), sig)
        else:
            (configuration.socket_directory / "worker.sock").touch()
        await stopped.wait()
        worker_stopped.set()
        Store(configuration.state_file).put(
            "run_stop", "end", {"reason": "operator_stop"}
        )

    monkeypatch.setattr(benchmark, "DockerFixture", Harness)
    monkeypatch.setattr(benchmark, "run", worker)
    with pytest.raises(asyncio.CancelledError):
        await benchmark.run_campaign(config, live=True)
    assert closed == [True]
    if stage == "character":
        assert not workers
    else:
        assert worker_stopped.is_set()
    if stage == "start_game":
        assert startup_saw_stop == [True]


@pytest.mark.parametrize(
    "reason",
    [
        "observation_stale",
        "world_changed",
        "startup_timeout",
        "completed",
        "deaths_limit",
        "stalled",
        "proposal_timeout",
        None,
    ],
)
async def test_budget_does_not_hide_critical_stop(tmp_path, monkeypatch, reason):
    config = runtime.Configuration(
        provider="native",
        mode="shadow",
        bots=[7],
        socket_directory=tmp_path,
        state_file=tmp_path / "state.db",
        run_seconds=10,
        benchmark_supervision=True,
        recording={"path": tmp_path / "replay.db", "namespace": "priority"},
    )
    state = Store(config.state_file)
    state.put("budget_stop", "7", {"at": time.time()})
    now = time.monotonic()
    monkeypatch.setattr(
        runtime,
        "Stops",
        lambda **kw: Stops(start=now - 11, last=now, reason=reason, **kw),
    )
    await runtime.run(config, asyncio.Event())
    expected = (
        reason
        if reason in {"observation_stale", "world_changed", "startup_timeout"}
        else "budget_stop"
    )
    assert state.get("run_stop", "end")["reason"] == expected
