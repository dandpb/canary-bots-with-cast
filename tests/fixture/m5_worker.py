"""Free-only worker: no provider client, credentials or operator endpoint."""

import asyncio
import json
import sys
import time
from pathlib import Path

from canary_brain import runtime
from canary_brain.protocol import Observation

from m5_stop import Stops

WORK = Path(sys.argv[1])
MODE = sys.argv[2]
assert MODE in {"native", "fake"}
STOP = Stops(model=MODE == "fake")
TRACE = WORK / "supervisor.jsonl"
CURRENT = None


def forbidden(*_args, **_kwargs):
    raise AssertionError(
        "qualification cannot access credentials or a network provider"
    )


runtime.read_credential = forbidden
runtime.AsyncOpenAI = forbidden
BaseController = runtime.Controller


class Controller(BaseController):
    def __init__(self, *args, **kwargs):
        global CURRENT
        super().__init__(*args, **kwargs)
        CURRENT = self

    async def handle(self, packet):
        await super().handle(packet)
        if packet.get("type") in {"observation", "telemetry"}:
            if packet.get("type") == "observation":
                Observation.model_validate(packet)
            STOP.observe(packet, time.monotonic())

    def record(self, bot, kind, data, key=None):
        super().record(bot, kind, data, key)
        if kind == "decision":
            STOP.decision(data, time.monotonic())


class ScriptedFake(runtime.FakeProvider):
    async def decide(self, observation, memory=None):
        candidates = {a.id: a.action for a in observation.actions}
        if observation.bot.objective_running:
            return next(
                (k for k, v in candidates.items() if v == "continue"),
                next(iter(candidates)),
            )
        if observation.bot.potions < 10 and "resupply" in candidates:
            return "resupply"
        for preferred in ("hunt:399", "hunt:77", "resupply", "continue"):
            if preferred in candidates:
                return preferred
        return next(iter(candidates))


runtime.Controller = Controller
runtime.FakeProvider = ScriptedFake


async def main():
    config = runtime.Configuration.model_validate_json(
        (WORK / "worker.json").read_text()
    )
    assert (
        config.provider == MODE
        and config.credential_file is None
        and config.gateway is None
    )
    assert config.operator_port is None and config.run_seconds is None
    stop = asyncio.Event()
    task = asyncio.create_task(runtime.run(config, stop))
    launch = time.monotonic()
    try:
        while not task.done():
            now = time.monotonic()
            reason = STOP.check(now)
            if (
                CURRENT
                and CURRENT.recorder
                and (CURRENT.recorder.errors or CURRENT.recorder.dropped)
            ):
                reason = "recorder_error"
            if STOP.start is None and now - launch > 240:
                reason = "startup_timeout"
            value = {
                "monotonic": now,
                "start": STOP.start,
                "elapsed": now - STOP.start if STOP.start else None,
                "last": STOP.last,
                "deaths": STOP.deaths,
                "opportunity": STOP.opportunity,
                "reason": reason,
            }
            with TRACE.open("a") as stream:
                stream.write(json.dumps(value) + "\n")
            if reason:
                stop.set()
                break
            await asyncio.sleep(1)
        await task
    finally:
        stop.set()
        await asyncio.gather(task, return_exceptions=True)
        (WORK / "stop.json").write_text(
            json.dumps({**value, "finished": time.monotonic()})
        )


asyncio.run(main())
