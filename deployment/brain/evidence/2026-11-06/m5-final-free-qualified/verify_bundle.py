"""Verify the closed free-B appendix offline; paid admission remains false."""

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_archive(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate archive member")
        integrity = json.loads(archive.read("integrity.json"))
        require(integrity["version"] == 1, "unsupported archive version")
        require(
            set(integrity["sha256"]) == set(names) - {"integrity.json"},
            "archive index mismatch",
        )
        decoded = {}
        for name, expected in integrity["sha256"].items():
            require(
                name == "run.json"
                or (name.startswith("events-") and name.endswith(".json")),
                "unexpected archive member",
            )
            data = archive.read(name)
            require(
                hashlib.sha256(data).hexdigest() == expected, "archive hash changed"
            )
            decoded[name] = json.loads(data)
    metadata = decoded.pop("run.json")
    events = [event for name in sorted(decoded) for event in decoded[name]]
    require(
        len({event["key"] for event in events}) == len(events), "duplicate event key"
    )
    return metadata, events


def verify(root, repository=None):
    index = load(root / "checksums.json")
    present = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "checksums.json"
    }
    require(set(index) == present, "published inventory mismatch")
    for name, expected in index.items():
        path = root / name
        require(
            path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
            "unsafe published path",
        )
        require(sha(path) == expected, "published hash changed: " + name)
    report = load(root / "summary.json")
    require(
        report["free_qualification_accepted"] is True
        and report["paid_pilot_admitted"] is False,
        "qualification scope changed",
    )
    require(
        {row["mode"] for row in report["runs"]} == {"native", "fake"},
        "participant inventory changed",
    )
    expected = {
        "native": (3296, 1800387, 3891, 102691),
        "fake": (5750, 1801000, 4142, 102942),
    }
    for row in report["runs"]:
        mode = row["mode"]
        folder = root / mode
        archive = root / row["archive"]
        require(sha(archive) == row["archive_sha256"], "matrix archive hash changed")
        metadata, events = read_archive(archive)
        require(
            metadata["id"] == metadata["manifest"]["run_id"] == row["run_id"],
            "run identity changed",
        )
        require(
            metadata["status"] == row["recording_status"] == "completed",
            "run did not complete",
        )
        require(
            metadata["event_count"] == row["event_count"] == len(events),
            "event count changed",
        )
        require(
            metadata["duration_ms"]
            == row["recording_envelope_duration_ms"]
            == max(event["t_ms"] for event in events),
            "recording envelope changed",
        )
        samples = sorted(
            (event for event in events if event["kind"] == "sample"),
            key=lambda event: (event["t_ms"], event["id"]),
        )
        span = samples[-1]["t_ms"] - samples[0]["t_ms"]
        require(1800000 <= span <= 1805000, "sampled horizon outside declared bounds")
        require(
            span == round(row["sampled_span_seconds"] * 1000), "sampled span changed"
        )
        require(
            not any(
                event["kind"] in {"gap", "request", "operator"} for event in events
            ),
            "gap, inference or intervention recorded",
        )
        require(
            row["requested_seconds"] == 1800
            and row["free_qualification_accepted"] is True
            and row["paid_pilot_admitted"] is False,
            "participant scope changed",
        )
        require(
            len(row["checks"]) == 16
            and all(value is True for value in row["checks"].values()),
            "16 gates did not pass",
        )
        for stop in row["supervisor"]:
            require(
                stop["reason"] == "completed"
                and 1800 <= stop["observed_seconds"] <= 1805
                and 1800 <= stop["elapsed_seconds"] <= 1805,
                "supervisor horizon changed",
            )
        first = samples[0]["data"]["bot"]["xp"]
        last = samples[-1]["data"]["bot"]["xp"]
        saved = load(folder / "saved-character.json")
        require(first == row["initial_xp"] == 98800, "initial XP changed")
        require(
            last == row["last_sample_xp"] == row["saved_xp"] == saved["experience"],
            "saved XP mismatch",
        )
        require(
            (len(events), span, last - first, saved["experience"]) == expected[mode],
            "expected result changed",
        )
        require(
            set(saved) == {"experience", "id", "level", "posx", "posy", "posz"},
            "saved SQL projection changed",
        )
        require(
            all(
                row["metrics"][key] == 0
                for key in (
                    "deaths",
                    "gaps",
                    "interventions",
                    "automatic_recoveries_requested",
                    "spent_nanousd",
                    "reserved_nanousd",
                )
            ),
            "zero observed metrics changed",
        )
        require(
            row["application_source_revision"]
            == metadata["manifest"]["source_revision"]
            == "47adddc40ad866e75450d317622dada6b7592687",
            "producer source changed",
        )
        require(
            sha(folder / "producer-driver.py")
            == "6f3c8fc550b24511fbd0d30c2ebe7611a1e977a7006fcbcae39343ed791c1336",
            "exact driver source changed",
        )
        require(
            row["native_source_revision"] == "d43050147bc13d8024bdc66b641b127c31253b7c",
            "native source changed",
        )
        require(
            row["fixture_sha256"]
            == metadata["manifest"]["initial_sha256"]
            == "42467745d544801e44e32deecf99f5f6d1e1aa869e2bf227734daf95ae42e5be",
            "equivalent fixture changed",
        )
        require(row["cycle"]["complete"] is True, "cycle not established")
        live = [
            json.loads(line)
            for line in gzip.decompress(
                (folder / "character-live.jsonl.gz").read_bytes()
            )
            .decode()
            .splitlines()
        ]
        require(len(live) > 0, "memory observations missing")
        cleanup = load(folder / "cleanup-receipt.json")
        require(
            cleanup["resources_cleaned"] is True
            and cleanup["containers"] == cleanup["networks"] == [],
            "cleanup failed",
        )
        audit = load(folder / "postrun-audit-receipt.json")
        require(
            audit["independent_scoped_absence_verified"] is True
            and audit["requests"] == 0,
            "post-run absence or request count changed",
        )
        if mode == "fake":
            completions = [
                event
                for event in events
                if event["kind"] == "outcome"
                and event["data"].get("status") == "completed"
                and event["data"].get("reason") == "hunt_progress"
            ]
            require(
                len(completions) == row["metrics"]["completed_actions"] == 5,
                "hunt completions changed",
            )
            require(
                all(event["data"]["metrics"]["xp_delta"] > 0 for event in completions),
                "completed hunt lacks positive XP",
            )
            require(
                row["metrics"]["confirmed_objective_defeats"] == 108,
                "confirmed defeats changed",
            )
    preserved = 0
    if repository is not None:
        proof = load(root / "previous-evidence-preservation.json")
        for reference in (proof["baseline_pr25_head"], "HEAD"):
            output = subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(repository),
                    "ls-tree",
                    "-r",
                    reference,
                    "--",
                    "deployment/brain/evidence",
                ],
                text=True,
            )
            tree = {
                line.split("\t", 1)[1]: line.split("\t", 1)[0].split()[-1]
                for line in output.splitlines()
            }
            require(
                all(tree.get(row["path"]) == row["git_blob"] for row in proof["files"]),
                "previous evidence Git blob changed",
            )
        for row in proof["files"]:
            require(
                sha(repository / row["path"]) == row["sha256"],
                "previous evidence bytes changed",
            )
        preserved = len(proof["files"])
        require(
            preserved == proof["unchanged_previous_evidence_blobs"] == 326,
            "previous evidence count changed",
        )
    return {
        "verified_files": len(index),
        "events": {row["mode"]: row["event_count"] for row in report["runs"]},
        "free_qualification_accepted": True,
        "paid_pilot_admitted": False,
        "previous_evidence_blobs_checked": preserved,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                verify(Path(__file__).resolve().parent, args.repository), sort_keys=True
            )
        )
    except (
        ValueError,
        KeyError,
        OSError,
        zipfile.BadZipFile,
        subprocess.CalledProcessError,
    ) as error:
        print("Evidence verification failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
