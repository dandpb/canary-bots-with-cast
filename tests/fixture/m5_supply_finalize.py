"""Accept actual solo purchase AND explicit return; never count as a timed run."""

import json
import sys
from pathlib import Path

from canary_brain.recording import RecordingStore
from m5_report import report

work = Path(sys.argv[1])
result = json.loads((work / "result.json").read_text())
manifest = json.loads((work.parent / "manifest.json").read_text())
assert result["phase"] == "finished" and manifest["purpose"].startswith("supply-only")
initial = json.loads((work / "initial-supplies.json").read_text())
saved = json.loads((work / "saved-supplies.json").read_text())
goal = (
    json.loads((work / "supply-goal.json").read_text())
    if (work / "supply-goal.json").is_file()
    else {}
)
data = report(work)
character = result["saved_character"]
home = result["initial_character"]
returned = (
    character["posz"] == home["posz"]
    and max(abs(character[k] - home[k]) for k in ["posx", "posy"]) <= 3
)
checks = {
    "goal_stop": result["stop"]["reason"] == "supply_goal_completed",
    "authoritative_purchase": goal.get("purchase", {})
    .get("metrics", {})
    .get("supply_delta", 0)
    >= 38,
    "authoritative_return": goal.get("return", {}).get("status") == "completed"
    and goal.get("return", {}).get("reason")
    in {"party_rejoined", "supplies_bought_and_party_rejoined"},
    "stock_persisted": initial["potions"] == 2 and saved["potions"] == 40,
    "bank_debit_persisted": initial["bank"] == 10000 and saved["bank"] == 7986,
    "saved_near_initial_temple": returned,
    "no_recorded_gaps": data["metrics"]["gaps"] == 0,
    "zero_inference_requests": data["ledger"]["requests"] == 0,
}
data.update(
    attempt=result,
    checks=checks,
    supply_gate_passed=all(checks.values()),
    initial_supplies=initial,
    saved_supplies=saved,
    goal=goal,
    scope="Separate low-stock derivative; not a 30-minute equivalent-start result.",
)
RecordingStore(work / "recording.sqlite3").finish(
    data["run_id"], "completed" if all(checks.values()) else "failed"
)
with (work / "analysis.json").open("x") as stream:
    json.dump(data, stream, indent=2)
print(
    json.dumps(
        {
            "run_id": data["run_id"],
            "checks": checks,
            "observed_seconds": data["observed_seconds"],
        },
        indent=2,
    )
)
if not all(checks.values()):
    raise SystemExit(1)
