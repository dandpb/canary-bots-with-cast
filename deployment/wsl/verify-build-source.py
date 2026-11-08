"""Require the mounted native source to match its advertised clean Git revision."""

import argparse
import json
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
    if git("status", "--porcelain", "--untracked-files=normal"):
        raise RuntimeError("native build requires a clean source tree")
    return {"source_revision": revision, "source_clean": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.source, args.revision)))


if __name__ == "__main__":
    main()
