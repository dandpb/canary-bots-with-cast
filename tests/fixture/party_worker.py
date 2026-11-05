"""Production offline worker with QA-only counters; no API credentials or network providers."""

import asyncio
import collections
import json
import os
import resource
import time
from pathlib import Path

from canary_brain import runtime

COUNTS = collections.Counter()
CURRENT = None
PEAK_PENDING = 0
OUTCOMES = []


class MeasuredController(runtime.Controller):
    async def handle(self, packet):
        global CURRENT, PEAK_PENDING
        CURRENT = self
        COUNTS[packet.get("type", "unknown")] += 1
        if packet.get("type") == "outcome":
            OUTCOMES.append(packet)
        await super().handle(packet)
        PEAK_PENDING = max(PEAK_PENDING, len(self.pending))


runtime.Controller = MeasuredController


async def sample():
    while True:
        c = CURRENT
        usage = resource.getrusage(resource.RUSAGE_SELF)
        data = {
            "at": time.monotonic(),
            "pid": os.getpid(),
            "cpu_seconds": usage.ru_utime + usage.ru_stime,
            "rss_kib_peak": usage.ru_maxrss,
            "packets": dict(COUNTS),
            "pending_peak": PEAK_PENDING,
            "pending": len(c.pending) if c else 0,
            "outcomes": OUTCOMES[-100:],
            "bots": {str(guid): obs.model_dump() for guid, obs in c.latest.items()}
            if c
            else {},
        }
        target = Path("/canary/party-worker-metrics.json")
        target.with_suffix(".tmp").write_text(json.dumps(data))
        target.with_suffix(".tmp").replace(target)
        await asyncio.sleep(1)


async def main():
    Path("/canary/party-worker.pid").write_text(str(os.getpid()))
    task = asyncio.create_task(sample())
    try:
        configuration = runtime.Configuration.model_validate_json(
            Path("/qa/worker.json").read_text()
        )
        assert (
            configuration.provider == "fake" and configuration.credential_file is None
        )
        await runtime.run(configuration)
    finally:
        task.cancel()


asyncio.run(main())
