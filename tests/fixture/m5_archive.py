"""Export only finalized attempts, with immutable source and recording evidence."""

import gzip
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from canary_brain.recording import ReplayReader
from canary_brain.replay import export_archive
from m5_cycle_report import report as cycle_report

ROOT = Path(__file__).resolve().parents[2]
work = Path(sys.argv[1])
analysis = json.loads((work / "analysis.json").read_text())
manifest = json.loads((work.parent / "manifest.json").read_text())
assert analysis["attempt"]["phase"] == "finished"
assert analysis["manifest"]["initial_sha256"] == manifest["fixture_sha256"]
assert analysis["ledger"]["requests"] == 0
output = (
    ROOT
    / "deployment/brain/evidence/2026-11-05/m5-free-qualification"
    / work.parent.name
    / work.name
)
output.mkdir(parents=True, exist_ok=False)
(output / "cycles.json").write_text(json.dumps(cycle_report(work), indent=2))
for source in [
    work / "analysis.json",
    work / "result.json",
    work.parent / "manifest.json",
    work / "worker.json",
    work / "config/server.json",
    work / "compose.json",
]:
    shutil.copyfile(source, output / source.name)
for name in [
    "supervisor.jsonl",
    "character-live.jsonl",
    "phase-status.jsonl",
    "services.log",
    "worker.log",
]:
    source = work / name
    if source.is_file():
        (output / (name + ".gz")).write_bytes(
            gzip.compress(source.read_bytes(), mtime=0)
        )
for name in [
    "supply-goal.json",
    "supply-purchase.json",
    "initial-supplies.json",
    "saved-supplies.json",
    "platform-attestation.json",
]:
    if (work / name).is_file():
        shutil.copyfile(work / name, output / name)
verified = {}
for name, expected in manifest["harness_sha256"].items():
    blob = subprocess.check_output(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            manifest["source_revision"] + ":tests/fixture/" + name,
        ]
    )
    actual = hashlib.sha256(blob).hexdigest()
    assert actual == expected, (name, actual, expected)
    verified[name] = actual
(output / "frozen-source.json").write_text(
    json.dumps(
        {"revision": manifest["source_revision"], "verified_git_blobs": verified},
        indent=2,
    )
)
export_archive(
    ReplayReader(work / "recording.sqlite3"),
    analysis["run_id"],
    output / "run.replay.zip",
)
(output / "checksums.json").write_text(
    json.dumps(
        {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in output.iterdir()
            if p.is_file()
        },
        indent=2,
    )
)
print(output)
