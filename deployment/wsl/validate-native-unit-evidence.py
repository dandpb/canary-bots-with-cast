"""Validate closed native PlayerStorage GoogleTest evidence; never run a target."""

import argparse
import hashlib
import json
import platform
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


REQUIRED = {
    "QueuedCheckpointAcknowledgementsRetainUpsertABA",
    "AcknowledgingOldDeletionRetainsDeleteReinsertDelete",
    "MissingRevisionAndEmptyAcknowledgementsFailClosed",
    "ClearAndIngestDoNotRecycleCheckpointRevisions",
    "RegeneratedReservedKeyReplacesPendingDeletion",
}


def validate(evidence: Path, revision: str, release_core: Path, release_lib: Path) -> dict:
    if platform.machine().lower() not in {"aarch64", "arm64"}:
        raise ValueError("native unit evidence requires an ARM64 executor")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("full SOURCE_REVISION required")
    names = set()
    in_suite = False
    for line in (evidence / "tests.txt").read_text().splitlines():
        if line and not line[0].isspace():
            in_suite = line == "PlayerStorageTest."
        elif in_suite and line.strip():
            name = line.strip()
            if not re.fullmatch(r"[A-Za-z0-9_]+", name) or name in names:
                raise ValueError("invalid/duplicate listed test")
            names.add(name)
    if not names or not REQUIRED <= names or any("DISABLED_" in n for n in names):
        raise ValueError("empty, disabled or missing required regression selection")
    root = ET.parse(evidence / "results.xml").getroot()
    cases = root.findall(".//testcase")
    actual = set()
    for case in cases:
        name = case.get("name")
        if (case.get("classname") != "PlayerStorageTest" or name in actual
                or case.get("status") != "run" or case.get("result") != "completed"
                or any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))):
            raise ValueError("unexpected, duplicate or unsuccessful test case")
        actual.add(name)
    if actual != names or int(root.get("tests", "-1")) != len(names):
        raise ValueError("listed/XML test selection mismatch")
    if any(int(root.get(key, "-1")) != 0 for key in ("failures", "errors", "disabled")):
        raise ValueError("GoogleTest summary is not clean")
    identities = {}
    for label, path in (("canary_ut", evidence / "canary_ut"),
                        ("release_canary", release_core), ("release_bot_engine", release_lib)):
        with path.open("rb") as stream:
            header = stream.read(20)
        if (header[:6] != b"\x7fELF\x02\x01" or len(header) != 20
                or struct.unpack_from("<H", header, 18)[0] != 183):
            raise ValueError(f"{label} is not ELF64 little-endian AArch64")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        identities[label] = {"sha256": digest, "bytes": path.stat().st_size, "elf_machine": 183}
    for name in ("tests.txt", "results.xml", "run.log"):
        with (evidence / name).open("rb") as stream:
            identities[name] = {"sha256": hashlib.file_digest(stream, "sha256").hexdigest()}
    return {"source_revision": revision, "executor_machine": platform.machine(),
            "tests": sorted(names), "test_count": len(names), "files": identities,
            "scope": "Native PlayerStorageTest only; not full-game, ISA baseline or runtime-pair qualification"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--release-core", type=Path, required=True)
    parser.add_argument("--release-lib", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.evidence, args.revision, args.release_core, args.release_lib)
    # Write only after every check succeeds; failed builds cannot export PASS metadata.
    (args.evidence / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
