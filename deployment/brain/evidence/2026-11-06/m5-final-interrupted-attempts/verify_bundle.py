"""Stdlib-only offline check; writes nothing and executes no replay payload."""

import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
checksums = json.loads((root / "checksums.json").read_text())
for relative, expected in checksums.items():
    path = root / relative
    assert path.resolve().is_relative_to(root.resolve()) and path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, relative
overview = json.loads((root / "summary.json").read_text())
assert overview["accepted"] is False and overview["paid_pilot_admitted"] is False
events_count = {}
for mode in ["native", "fake"]:
    folder = root / mode
    with zipfile.ZipFile(folder / (mode + ".replay.zip")) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)) and len(names) <= 10002
        assert sum(i.file_size for i in archive.infolist()) <= 512 * 1024 * 1024
        integrity = json.loads(archive.read("integrity.json"))
        assert set(integrity["sha256"]) == set(names) - {"integrity.json"}
        for name, expected in integrity["sha256"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected
        run = json.loads(archive.read("run.json"))
        assert run["status"] == "interrupted" and not run["incomplete"]
        events = [
            e
            for name in sorted(names)
            if name.startswith("events-")
            for e in json.loads(archive.read(name))
        ]
    samples = [e for e in events if e["kind"] == "sample"]
    assert (samples[-1]["t_ms"] - samples[0]["t_ms"]) / 1000 < 1800
    producer = json.loads((folder / "producer-attestation.json").read_text())
    assert (
        hashlib.sha256((folder / "producer-driver.py").read_bytes()).hexdigest()
        == producer["driver_sha256"]
    )
    reviewed = json.loads((folder / "reviewed-qualification.json").read_text())
    assert (
        reviewed["accepted"] is False
        and reviewed["checks"]["positive_xp_observed"] is True
    )
    assert not json.loads((folder / "producer-resources-cleaned.json").read_text())[
        "resources_cleaned"
    ]
    assert json.loads((folder / "resources-observed-later.json").read_text())[
        "resources_absent"
    ]
    copied = json.loads((folder / "postmortem-copy-integrity.json").read_text())
    later = json.loads((folder / "postmortem-source-final-integrity.json").read_text())
    assert (
        copied["source_before"]
        == copied["copied_before_start"]
        == copied["source_after_copy"]
        == later["source_after_forensic_query"]
    )
    assert later["temporary_db_removed_observed_later"]
    saved = json.loads(
        (folder / "postmortem-saved-character-postmortem.json").read_text()
    )["character"]
    assert saved["experience"] == samples[-1]["data"]["bot"]["xp"]
    events_count[mode] = len(events)
print(
    json.dumps(
        {
            "verified_files": len(checksums),
            "replay_events": events_count,
            "accepted": False,
            "paid_pilot_admitted": False,
        }
    )
)
