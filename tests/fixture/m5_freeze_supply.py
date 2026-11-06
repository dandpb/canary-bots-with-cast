"""Freeze the unstarted supply derivative's current driver and platform identity."""

import json
import sys
from pathlib import Path

from m5_qa import ROOT, command, sha

work = Path(sys.argv[1])
assert not any((work / mode).exists() for mode in ["native", "fake"])
manifest = json.loads((work / "manifest.json").read_text())
assert manifest["purpose"].startswith("supply-only")
manifest["parent_source_revision"] = manifest["source_revision"]
manifest["source_revision"] = command("git", "-C", ROOT, "rev-parse", "HEAD")
manifest["harness_sha256"] = {
    n: sha(ROOT / "tests/fixture" / n)
    for n in ["m5_qa.py", "m5_worker.py", "m5_stop.py"]
}
manifest["database_image_id"] = command(
    "docker", "image", "inspect", "mariadb:11.4", "--format", "{{.Id}}"
)
actual = command(
    "docker",
    "run",
    "--rm",
    "--network",
    "none",
    "--entrypoint",
    "sha256sum",
    manifest["image_id"],
    "/canary/canary",
    "/canary/libbot_engine.so",
)
assert {
    Path(path).name: digest
    for digest, path in (line.split() for line in actual.splitlines())
} == manifest["binary_sha256"]
manifest["binary_attestation"] = (
    "sha256sum inside the pinned game image, before execution"
)
(work / "manifest.json").write_text(json.dumps(manifest, indent=2))
print(
    json.dumps(
        {
            k: manifest[k]
            for k in ["source_revision", "database_image_id", "fixture_sha256"]
        }
    )
)
