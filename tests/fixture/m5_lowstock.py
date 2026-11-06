"""Declare a separately hashed supply-only derivative, never alter a timed run."""

import json
import shutil
import sys
from pathlib import Path

from canary_brain.benchmark import fixture_hash
from m5_qa import WORLD, sha

source, target = map(Path, sys.argv[1:])
target.mkdir(mode=0o700, exist_ok=False)
shutil.copytree(source / "fixture", target / "fixture")
path = target / "fixture/database.sql"
sql = path.read_text()
for item, sid in [(266, 201), (268, 202)]:
    before = f"(65001,103,{sid},{item},20,'')"
    assert sql.count(before) == 1
    sql = sql.replace(before, f"(65001,103,{sid},{item},1,'')")
path.write_text(sql)
manifest = json.loads((source / "manifest.json").read_text())
manifest["purpose"] = "supply-only derivative; excluded from equivalent 1800s windows"
manifest["parent_fixture_sha256"] = manifest["fixture_sha256"]
manifest["fixture_sha256"] = fixture_hash(target / "fixture", WORLD)
manifest["potions"] = {266: 1, 268: 1}
manifest["files"] = {
    str(p.relative_to(target / "fixture")): sha(p)
    for p in (target / "fixture").rglob("*")
    if p.is_file()
}
(target / "manifest.json").write_text(json.dumps(manifest, indent=2))
print(
    json.dumps(
        {k: manifest[k] for k in ["purpose", "fixture_sha256", "parent_fixture_sha256"]}
    )
)
