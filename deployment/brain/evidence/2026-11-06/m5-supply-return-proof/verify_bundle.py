"""Verify this narrow supply goal proof offline, without benchmark acceptance."""

import hashlib
import json
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


def verify(root):
    index = load(root / "checksums.json")
    present = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "checksums.json"
    }
    require(set(index) == present, "published inventory changed")
    for name, expected in index.items():
        path = root / name
        require(
            path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
            "unsafe published path",
        )
        require(sha(path) == expected, "published hash changed: " + name)
    summary = load(root / "summary.json")
    goal = load(root / "goal-proof.json")
    plan = load(root / "proof-plan.json")
    require(
        summary["qualification_accepted"] is False
        and summary["paid_pilot_admitted"] is False,
        "benchmark verdict changed",
    )
    require(
        goal["goal_accepted"] is True
        and len(goal["checks"]) == 14
        and all(value is True for value in goal["checks"].values()),
        "goal checks changed",
    )
    require(
        summary["application_source_revision"]
        == plan["application_source_revision"]
        == "390b8c8920d4e42e8d2eaca056c2076798d1edf7",
        "application source changed",
    )
    require(
        summary["native_source_revision"]
        == plan["native_source_revision"]
        == "d43050147bc13d8024bdc66b641b127c31253b7c",
        "native source changed",
    )
    require(
        plan["fixture_variation"]["changes"]["hunt_mask_after"] == [],
        "controlled mask changed",
    )
    require(
        plan["fixture_variation"]["changes"]["health_potion_stack"]
        == plan["fixture_variation"]["changes"]["mana_potion_stack"]
        == 1,
        "low stock derivative changed",
    )
    require(
        goal["initial_supplies"] == {"bank": 10000, "potions": 2},
        "initial supplies changed",
    )
    require(
        goal["saved_supplies"] == {"bank": 7986, "potions": 40},
        "saved supplies changed",
    )
    saved = goal["saved_character"]
    require(
        [saved[key] for key in ("posx", "posy", "posz")] == [32371, 32238, 7]
        and saved["experience"] == 98800,
        "saved position or XP changed",
    )
    archive_path = root / "supply-b.replay.zip"
    require(
        sha(archive_path) == summary["archive_sha256"], "summary archive hash changed"
    )
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate archive member")
        integrity = json.loads(archive.read("integrity.json"))
        require(integrity["version"] == 1, "unsupported archive version")
        require(
            set(integrity["sha256"]) == set(names) - {"integrity.json"},
            "archive inventory mismatch",
        )
        decoded = {}
        for name, expected in integrity["sha256"].items():
            value = archive.read(name)
            require(
                hashlib.sha256(value).hexdigest() == expected, "archive hash mismatch"
            )
            decoded[name] = json.loads(value)
    metadata = decoded.pop("run.json")
    events = [event for name in sorted(decoded) for event in decoded[name]]
    require(
        metadata["id"] == summary["run_id"] == "m5-supply-7f445fec33:supply",
        "run identity changed",
    )
    require(
        len(events) == metadata["event_count"] == summary["event_count"] == 207,
        "event count changed",
    )
    samples = sorted(
        [event for event in events if event["kind"] == "sample"],
        key=lambda event: (event["t_ms"], event["id"]),
    )
    require(
        samples[-1]["t_ms"] - samples[0]["t_ms"] == summary["sampled_span_ms"] == 82749,
        "sampled horizon changed",
    )
    require(
        not any(event["kind"] in {"request", "gap", "operator"} for event in events),
        "inference, gap or operator event appeared",
    )
    require(
        all(
            summary["metrics"][key] == 0
            for key in (
                "deaths",
                "gaps",
                "interventions",
                "automatic_recoveries_requested",
                "spent_nanousd",
                "reserved_nanousd",
            )
        ),
        "zero-observed metric changed",
    )
    for name, reason, elapsed in (
        ("purchase.json", "supplies_bought", 44.647),
        ("return.json", "party_rejoined", 38.205),
    ):
        outcome = load(root / name)
        require(
            outcome["status"] == "completed"
            and outcome["reason"] == reason
            and outcome["metrics"]["elapsed_seconds"] == elapsed,
            "goal outcome changed",
        )
        require(outcome["metrics"]["party_size"] == 1, "solo goal changed")
        require(
            len(
                [
                    event
                    for event in events
                    if event["kind"] == "outcome" and event["data"] == outcome
                ]
            )
            == 1,
            "linked goal outcome missing",
        )
    return {
        "verified_files": len(index),
        "events": len(events),
        "goal_checks": 14,
        "goal_accepted": True,
        "qualification_accepted": False,
        "paid_pilot_admitted": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        print("Evidence verification failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
