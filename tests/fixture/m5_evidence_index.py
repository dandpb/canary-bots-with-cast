"""Assemble published free-run evidence without reading DB/provider env files."""

import hashlib
import json
from pathlib import Path

from m5_cycle_report import report as cycles

ROOT = Path(__file__).resolve().parents[2]
output = ROOT / "deployment/brain/evidence/2026-11-05/m5-free-qualification"
rows = []
for name, mode in [
    ("b", "native"),
    ("d", "native"),
    ("d", "fake"),
    ("e", "fake"),
    ("f", "fake"),
]:
    work = Path("/tmp/m5q-20261105" + name) / mode
    target = output / work.parent.name / mode
    analysis = json.loads((target / "analysis.json").read_text())
    if not (target / "cycles.json").exists():
        (target / "cycles.json").write_text(json.dumps(cycles(work), indent=2))
    attestation = {
        "game_image_id": json.loads((target / "manifest.json").read_text())["image_id"],
        "database_image_id": "sha256:a794d9eb009e20de605858a11f32f63b4075cbd197c650436f0e3b457e4caed7"
        if name in {"e", "f"} or (name == "d" and mode == "fake")
        else None,
        "database_evidence": "Pinned by content ID before execution"
        if name in {"e", "f"}
        else "Actual database container .Image inspected during fake D before teardown"
        if name == "d" and mode == "fake"
        else "Original Compose used mariadb:11.4; actual container digest was not collected before teardown. Do not infer it retrospectively from the current tag.",
        "game_binary_attestation": "Pinned D image checked independently with sha256sum inside a --network none container; both binaries match the manifest"
        if name in {"d", "e", "f"}
        else "Original image ID is build authority; external native-artifact hashes alone are not an in-image attestation",
    }
    (target / "platform-attestation.json").write_text(json.dumps(attestation, indent=2))
    (target / "checksums.json").write_text(
        json.dumps(
            {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in target.iterdir()
                if p.is_file() and p.name != "checksums.json"
            },
            indent=2,
        )
    )
    rows.append(
        {
            "run_id": analysis["run_id"],
            "artifact": str(target.relative_to(output)),
            "stop": analysis["attempt"]["stop"]["reason"],
            "supervisor_seconds": analysis["attempt"]["stop"]["elapsed"],
            "recorded_seconds": analysis["observed_seconds"],
            "xp_delta": analysis["metrics"]["xp_delta"],
            "deaths": analysis["metrics"]["deaths"],
            "gaps": analysis["metrics"]["gaps"],
            "inference_requests": analysis["ledger"]["requests"],
            "timed_gate_passed": analysis.get("timed_gate_passed"),
            "supply_gate_passed": analysis.get("supply_gate_passed"),
            "database_attested": attestation["database_image_id"] is not None,
        }
    )
index = {
    "date": "2026-11-05",
    "attempts": rows,
    "paid_execution_ready": False,
    "limits": [
        "Controlled routes and normal live-world nondeterminism; no provider/model quality ranking.",
        "Long-window native D database image digest was not captured; both historical Compose files name a mutable tag. Future paired scored runs require pinned database content IDs.",
        "Low-stock supply proof is a distinct fixture and scripted resupply + retreat sequence, not a purchase inside the long-window cohort or an automatic solo resupply return.",
        "Long windows use frozen QA driver c03a3225, not the revised canonical runner in PR26.",
        "PR26 requires independent re-review; Haiku native strict wire gate in PR27 is unresolved.",
        "Real account access, current monthly ledger and paid opt-in remain unverified; no credentials were read.",
    ],
}
(output / "index.json").write_text(json.dumps(index, indent=2))
print(json.dumps(index, indent=2))
