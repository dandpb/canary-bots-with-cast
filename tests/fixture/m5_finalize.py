"""Finalize metadata only after the private harness has stopped and saved its DB."""

import json
import sys
from pathlib import Path

from canary_brain.recording import RecordingStore
from m5_report import report

work = Path(sys.argv[1])
result = json.loads((work / "result.json").read_text())
assert result["phase"] == "finished", "do not finalize an active or provisioning run"
stop = result["stop"]
data = report(work)
progression = data.get("progression", {})
window = progression.get("window") or {}
native_seconds = window.get("native_seconds")
duration_ok = (
    type(native_seconds) in (int, float)
    and 1800 <= native_seconds <= 1805
    and 1800 <= data.get("observed_seconds", 0) <= 1805
)
finished = stop["reason"] == "completed"
data["checks"] = {
    "horizon_completed": finished,
    "observed_duration_ok": duration_ok,
    "no_recorded_gaps": data["metrics"]["gaps"] == 0
    and data.get("recording_incomplete") is False,
    "positive_recorded_xp": window.get("xp_delta", 0) > 0,
    "window_and_persistence_verified": bool(window) and progression.get("errors") == [],
    "zero_inference_requests": all(
        data["ledger"].get(key) == 0
        for key in ("requests", "spent_nanousd", "reserved_nanousd")
    ),
}
data["attempt"] = result
data["timed_gate_passed"] = all(data["checks"].values())
status = "completed" if data["timed_gate_passed"] else "failed"
RecordingStore(work / "recording.sqlite3").finish(data["run_id"], status)
data["recording_status"] = status
with (work / "analysis.json").open("x") as stream:
    json.dump(data, stream, indent=2)
print(
    json.dumps(
        {
            "run_id": data["run_id"],
            "checks": data["checks"],
            "stop": stop["reason"],
            "observed_seconds": data["observed_seconds"],
        },
        indent=2,
    )
)
if not data["timed_gate_passed"]:
    raise SystemExit(1)
