"""Validate exported hashes/replay imports and exact owned-project teardown."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from canary_brain.recording import ReplayReader
from canary_brain.replay import import_archive

root = (
    Path(__file__).resolve().parents[2]
    / "deployment/brain/evidence/2026-11-05/m5-free-qualification"
)
checked = 0
archives = []
projects = []
for checksums in sorted(root.rglob("checksums.json")):
    directory = checksums.parent
    for name, expected in json.loads(checksums.read_text()).items():
        assert (
            hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected
        ), (directory, name)
        checked += 1
    with tempfile.TemporaryDirectory(prefix="m5import-") as temporary:
        destination = Path(temporary) / "replay.db"
        run = import_archive(directory / "run.replay.zip", destination)
        metadata = ReplayReader(destination).run(run)
        archives.append(
            {
                "run_id": run,
                "status": metadata["status"],
                "incomplete": metadata["incomplete"],
            }
        )
    if (directory / "result.json").is_file():
        projects.append(json.loads((directory / "result.json").read_text())["project"])
    else:
        projects.append(
            "canary-bench-"
            + hashlib.sha256(b"m5-runner-free-smoke:native:0").hexdigest()[:20]
        )
for project in projects:
    assert not subprocess.check_output(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            "label=com.docker.compose.project=" + project,
            "--quiet",
        ],
        text=True,
    ).strip(), project
assert len(archives) == 6
assert all(not a["incomplete"] for a in archives)
result = {
    "verified_file_hashes": checked,
    "verified_replay_imports": archives,
    "owned_projects_removed": sorted(set(projects)),
    "provider_credentials_included": False,
    "scope": "Only allowlisted exported artifacts; database.env and provider credential paths are excluded by the exporters.",
}
(root / "verification.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
