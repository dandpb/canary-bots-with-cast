"""Check this published appendix offline; never grants benchmark acceptance."""

import hashlib
import json
from pathlib import Path
import sys
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive_events(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate archive names")
        integrity = json.loads(archive.read("integrity.json"))
        require(integrity["version"] == 1, "unexpected integrity version")
        hashes = integrity["sha256"]
        require(
            set(hashes) == set(names) - {"integrity.json"}, "archive inventory mismatch"
        )
        decoded = {}
        for name, expected in hashes.items():
            require(
                name == "run.json"
                or (name.startswith("events-") and name.endswith(".json")),
                "unexpected archive member",
            )
            data = archive.read(name)
            require(
                hashlib.sha256(data).hexdigest() == expected,
                "archive member hash changed",
            )
            decoded[name] = json.loads(data)
    metadata = decoded.pop("run.json")
    events = [event for name in sorted(decoded) for event in decoded[name]]
    require(metadata["event_count"] == len(events), "archive count changed")
    require(
        len({event["key"] for event in events}) == len(events), "duplicate event key"
    )
    require(
        metadata["duration_ms"] == max(event["t_ms"] for event in events),
        "archive envelope changed",
    )
    return metadata, events


def verify(root):
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
        require(sha(path) == expected, "published hash mismatch: " + name)
    matrix = load(root / "matrix.json")
    require(
        matrix["qualification_accepted"] is False
        and matrix["paid_pilot_admitted"] is False,
        "blocked verdict changed",
    )
    expected = {
        "B": (145, 60608),
        "C": (134, 60338),
        "D": (463, 240745),
        "E": (299, 121111),
        "G": (481, 240618),
        "H": (207, 94179),
    }
    require(
        {row["case"] for row in matrix["diagnostics"]} == set(expected),
        "diagnostic inventory changed",
    )
    for row in matrix["diagnostics"]:
        case = row["case"]
        require(
            row["qualification_accepted"] is False
            and row["paid_pilot_admitted"] is False,
            "case incorrectly accepted",
        )
        path = root / row["replay"]
        require(sha(path) == row["archive_sha256"], "matrix archive hash changed")
        metadata, events = archive_events(path)
        require(
            metadata["id"] == row["run_id"] == metadata["manifest"]["run_id"],
            "run identity changed",
        )
        require(
            metadata["status"] == row["recording_status"], "recording state changed"
        )
        samples = sorted(
            (event for event in events if event["kind"] == "sample"),
            key=lambda event: (event["t_ms"], event["id"]),
        )
        require(len(samples) >= 2, "not enough samples")
        span = samples[-1]["t_ms"] - samples[0]["t_ms"]
        require(
            (len(events), span)
            == expected[case]
            == (row["event_count"], row["sampled_span_ms"]),
            "count or horizon changed",
        )
        require(
            not any(event["kind"] in {"request", "gap"} for event in events),
            "unexpected inference request or gap",
        )
        require(
            samples[0]["data"]["bot"]["position"] == row["first_position"],
            "initial position changed",
        )
        require(
            samples[-1]["data"]["bot"]["position"] == row["last_sample_position"],
            "last position changed",
        )
        require(
            samples[-1]["data"]["bot"]["xp"] == row["last_sample_xp"], "last XP changed"
        )
        linked = [
            event["data"]
            for event in events
            if event["kind"] == "outcome"
            and event["data"].get("action_id") == row["linked_action_id"]
            and event["data"].get("status") in {"completed", "failed"}
        ]
        require(
            linked == row["linked_terminal_outcomes"], "linked terminal outcome changed"
        )
        require(
            row["metrics"]["automatic_recoveries_requested"] == 0,
            "automatic recovery count changed",
        )
        require(
            row["metrics"]["interventions"] == (1 if case == "E" else 2),
            "operator setup count changed",
        )
        require(
            row["metrics"]["deaths"] == row["metrics"]["gaps"] == 0,
            "observed zero metrics changed",
        )
        require(
            row["arrival_proven"] is (case == "H"), "arrival interpretation changed"
        )
        if case in {"B", "G"}:
            require(
                len(linked) == 1
                and linked[0]["status"] == "failed"
                and linked[0]["reason"] == "return_route_unavailable",
                "failed return erased",
            )
            require(
                linked[0]["metrics"]["elapsed_seconds"]
                == (28.213 if case == "B" else 209.286),
                "failed return time changed",
            )
        elif case in {"C", "D", "E"}:
            require(linked == [], "new terminal outcome")
        if case == "H":
            require(
                metadata["status"] == "interrupted"
                and row["requested_horizon_completed"] is False,
                "interrupted horizon erased",
            )
            require(
                row["canonical_saved_character_present"] is False
                and row["saved_character_source"] == "postmortem-B",
                "postmortem relabeled canonical",
            )
            require(
                len(linked) == 1
                and linked[0]["status"] == "completed"
                and linked[0]["reason"] == "party_rejoined",
                "native completion missing",
            )
            require(
                linked[0]["metrics"]["elapsed_seconds"] == 71.501
                and linked[0]["metrics"]["party_size"] == 1,
                "solo native completion changed",
            )
            receipt = load(root / "H/postmortem-db-copy-receipt.json")
            hashes = receipt["source_hashes"]
            require(
                receipt["source_read_only"] is True
                and hashes["unchanged"] is True
                and hashes["files_hashed"] == 345,
                "source copy receipt changed",
            )
            require(
                hashes["before_tree_sha256"]
                == hashes["after_tree_sha256"]
                == "96d5cc58d7c69600c6dd0e8e78f53b3ae3ccfa57432ec693499f0ec5ff269aa0",
                "original tree identity changed",
            )
            saved = load(root / "H/saved-character.postmortem-b.json")
            require(
                [saved[key] for key in ("posx", "posy", "posz")] == [32369, 32238, 7]
                and saved["health"] == 365
                and saved["experience"] == 100793,
                "postmortem character changed",
            )
            require(
                row["saved_distance_chebyshev_to_temple"] == 3,
                "arrival distance changed",
            )
    return {
        "verified_files": len(index),
        "diagnostic_events": {
            row["case"]: row["event_count"] for row in matrix["diagnostics"]
        },
        "qualification_accepted": False,
        "paid_pilot_admitted": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        print("Evidence verification failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
