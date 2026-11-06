"""Inspect a free run without changing character state or the accounting ledger."""

import collections
import json
import sqlite3
import sys
from pathlib import Path

from canary_brain.recording import ReplayReader
from canary_brain.replay import summary


def report(directory):
    directory = Path(directory)
    reader = ReplayReader(directory / "recording.sqlite3")
    runs = reader.runs()
    assert len(runs) == 1
    identity = runs[0]["id"]
    with reader.snapshot() as snapshot:
        data = summary(snapshot, identity)
        events = list(snapshot.all_events(identity))
    samples = [e for e in events if e["kind"] == "sample"]
    proposals = [
        e
        for e in events
        if e["kind"] == "decision" and e["data"].get("phase") == "selected"
    ]
    offered = collections.Counter(
        a["id"] for s in samples for a in s["data"]["actions"]
    )
    telemetry = [
        e for e in events if e["kind"] == "lifecycle" and "deaths" in e["data"]
    ]
    with sqlite3.connect(
        f"file:{directory / 'worker.sqlite3'}?mode=ro", uri=True
    ) as db:
        requests = db.execute(
            "SELECT COUNT(*),COALESCE(SUM(spent),0),COALESCE(SUM(CASE WHEN spent IS NULL THEN reserved ELSE 0 END),0) FROM requests"
        ).fetchone()
    if not samples:
        return {"run_id": identity, "samples": 0}
    start, end = samples[0], samples[-1]
    return {
        "run_id": identity,
        "manifest": data["manifest"],
        "metrics": data["metrics"],
        "first_sample": start,
        "last_sample": end,
        "observed_seconds": (end["t_ms"] - start["t_ms"]) / 1000,
        "samples": len(samples),
        "events": len(events),
        "minimum_health_percent": min(e["data"]["bot"]["health"] for e in samples),
        "positions": len({tuple(e["data"]["bot"]["position"]) for e in samples}),
        "offered": dict(offered),
        "selected": collections.Counter(e["data"]["selected"] for e in proposals),
        "native_phases": collections.Counter(e["data"]["phase"] for e in telemetry),
        "ledger": dict(
            zip(
                ["requests", "spent_nanousd", "reserved_nanousd"], requests, strict=True
            )
        ),
    }


if __name__ == "__main__":
    print(json.dumps(report(sys.argv[1]), indent=2))
