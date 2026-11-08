"""Require the mounted native source to match its advertised clean Git revision."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


def verify(source: Path, expected: str) -> dict[str, object]:
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise RuntimeError("SOURCE_REVISION must be a full 40-character commit")

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(source), *args],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("native build requires readable Git metadata")
        return result.stdout.strip()

    revision = git("rev-parse", "--verify", "HEAD")
    if revision != expected:
        raise RuntimeError("native source revision differs from SOURCE_REVISION")
    metadata = Path(git("rev-parse", "--absolute-git-dir")).resolve()
    common = Path(git("rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = source / common
    if metadata != common.resolve() or (metadata / "objects/info/alternates").exists():
        raise RuntimeError(
            "native build requires a standalone clone without alternates"
        )
    if git("status", "--porcelain", "--untracked-files=normal"):
        raise RuntimeError("native build requires a clean source tree")
    # Index flags and preserved mtimes can hide changed bytes from git status.
    # Native Linux checkouts retain the exact committed bytes, including links.
    entries = subprocess.check_output(
        ["git", "-C", str(source), "ls-tree", "-rz", "HEAD"], timeout=30
    )
    count = 0
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        identity, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = identity.split()
        path = source / os.fsdecode(raw_path)
        if kind != b"blob":
            raise RuntimeError("native build does not accept unresolved submodules")
        if mode == b"120000" and path.is_symlink():
            payload = os.fsencode(os.readlink(path))
        elif (
            mode in (b"100644", b"100755") and path.is_file() and not path.is_symlink()
        ):
            payload = path.read_bytes()
        else:
            raise RuntimeError("native source file type differs from its Git tree")
        actual = hashlib.sha1(
            b"blob " + str(len(payload)).encode() + b"\0" + payload
        ).hexdigest()
        if actual != oid.decode():
            raise RuntimeError(
                "native source must be byte-exact; use a clean native Linux clone"
            )
        count += 1
    return {"source_revision": revision, "source_clean": True, "verified_files": count}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.source, args.revision)))


if __name__ == "__main__":
    main()
