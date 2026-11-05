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
duration_ok = 1795 <= data["observed_seconds"] <= 1805
finished = stop["reason"] == "completed"
data["checks"] = {
    "horizon_completed": finished,
    "observed_duration_ok": duration_ok,
    "no_recorded_gaps": data["metrics"]["gaps"] == 0,
    "positive_recorded_xp": data["metrics"]["xp_delta"] > 0,
    "saved_xp_matches_last_sample": result["saved_character"]["experience"]
    == data["last_sample"]["data"]["bot"]["xp"],
    "zero_inference_requests": data["ledger"]["requests"] == 0,
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
