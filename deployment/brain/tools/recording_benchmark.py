"""Bounded synthetic recorder overhead sample, not a game-tick guarantee."""

import json
import statistics
import tempfile
import time
from pathlib import Path

from canary_brain.recording import Manifest, Recorder, RecordingConfiguration


def main():
    with tempfile.TemporaryDirectory(prefix="recording-perf-") as tmp:
        path = Path(tmp) / "recording.db"
        recorder = Recorder(
            RecordingConfiguration(path=path, namespace="perf"),
            [
                Manifest(
                    run_id=f"perf:{bot}",
                    bot_id=bot,
                    lineage=f"perf:{bot}",
                    synthetic=True,
                    provider="fake",
                )
                for bot in (1, 2, 3)
            ],
        )
        elapsed = []
        started = time.perf_counter()
        for index in range(1000):
            before = time.perf_counter_ns()
            recorder.emit(
                index % 3 + 1,
                "decision",
                {
                    "phase": "requested",
                    "options": [f"hunt:{n}" for n in range(32)],
                    "fixture": "x" * 2048,
                },
            )
            elapsed.append((time.perf_counter_ns() - before) / 1000)
        recorder.close()
        print(
            json.dumps(
                {
                    "synthetic": True,
                    "events": 1000,
                    "bots": 3,
                    "enqueue_p50_us": statistics.median(elapsed),
                    "enqueue_p95_us": sorted(elapsed)[949],
                    "flush_inclusive_seconds": time.perf_counter() - started,
                    "recording_bytes": path.stat().st_size,
                    "health": recorder.health(),
                    "limitation": "Burst enqueue/write overhead only; not real-server or combat-tail latency.",
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
