"""Archive a completed free native runner smoke, excluding DB environments."""

import gzip
import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

from canary_brain.recording import ReplayReader
from canary_brain.replay import export_archive

root = Path(__file__).resolve().parents[2]
work = Path(sys.argv[1])
result = json.loads((work / "smoke-result.json").read_text())
assert result["status"] == "completed" and result["inference_requests"] == 0
assert (
    hashlib.sha256((work / "frozen-driver.py").read_bytes()).hexdigest()
    == result["driver_sha256"]
)
output = (
    root
    / "deployment/brain/evidence/2026-11-05/m5-free-qualification/runner-smoke"
    / work.name
)
output.mkdir(parents=True, exist_ok=False)
for name in ["smoke-result.json", "frozen-driver.py"]:
    shutil.copyfile(work / name, output / name)
for name in ["experiment.json", "summary.json"]:
    shutil.copyfile(work / "runs" / name, output / name)
trial = work / "runs/native-0"
for name in ["compose.json", "saved-character.json"]:
    shutil.copyfile(trial / name, output / name)
for name in ["services.log", "character-live.jsonl"]:
    if (trial / name).is_file():
        (output / (name + ".gz")).write_bytes(
            gzip.compress((trial / name).read_bytes(), mtime=0)
        )
with sqlite3.connect(f"file:{trial / 'worker.sqlite3'}?mode=ro", uri=True) as db:
    ending = json.loads(
        db.execute(
            "SELECT data FROM records WHERE kind='run_stop' AND key='end'"
        ).fetchone()[0]
    )
(output / "supervised-stop.json").write_text(json.dumps(ending, indent=2))
reader = ReplayReader(work / "runs/recording.sqlite3")
export_archive(reader, reader.runs()[0]["id"], output / "run.replay.zip")
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
