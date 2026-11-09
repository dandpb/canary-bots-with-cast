"""Verify published evidence offline; this does not admit a paid pilot.

Only Python's standard library is required. Optional --repository also checks the
unchanged historical working files and Git blobs. No file is written.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def member(root, name):
    result = (root / name).resolve()
    require(result.is_relative_to(root.resolve()), "path outside evidence directory")
    require(not (root / name).is_symlink(), "symlink in evidence directory")
    return result


def verify_archive(path, trial):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate archive member")
        integrity = json.loads(archive.read("integrity.json"))
        require(integrity["version"] == 1, "unsupported archive integrity version")
        hashes = integrity["sha256"]
        require(
            set(hashes) == set(names) - {"integrity.json"}, "archive index mismatch"
        )
        decoded = {}
        for name, expected in hashes.items():
            value = archive.read(name)
            require(
                hashlib.sha256(value).hexdigest() == expected, "archive hash mismatch"
            )
            decoded[name] = json.loads(value)
    metadata = decoded.pop("run.json")
    events = [event for name in sorted(decoded) for event in decoded[name]]
    require(metadata["id"] == trial["run_id"], "archive run identity changed")
    require(metadata["manifest"]["run_id"] == trial["run_id"], "manifest run mismatch")
    require(metadata["status"] == trial["recording_status"], "archive status changed")
    require(
        metadata["event_count"] == trial["event_count"] == len(events),
        "event count mismatch",
    )
    require(
        len({event["key"] for event in events}) == len(events), "duplicate event key"
    )
    require(
        max(event["t_ms"] for event in events)
        == trial["recording_envelope_duration_ms"],
        "recording envelope changed",
    )
    samples = [event for event in events if event["kind"] == "sample"]
    require(len(samples) >= 2, "not enough samples")
    span_ms = max(event["t_ms"] for event in samples) - min(
        event["t_ms"] for event in samples
    )
    require(
        span_ms == round(trial["sampled_span_seconds"] * 1000),
        "sampled horizon mismatch",
    )
    samples.sort(key=lambda event: (event["t_ms"], event["id"]))
    require(
        samples[0]["data"]["bot"]["xp"] == trial["initial_xp"], "initial XP changed"
    )
    require(
        samples[-1]["data"]["bot"]["xp"] == trial["last_sample_xp"], "final XP changed"
    )
    require(
        not any(event["kind"] in {"gap", "request"} for event in events),
        "unexpected gap or inference request",
    )
    return events


def verify_history(root, repository):
    proof = load(root / "historical-preservation.json")
    files = proof["files"]
    require(
        proof["unchanged_git_blobs"] == len(files) == 89, "historical count changed"
    )
    require(
        proof["historical_evidence_tree_unchanged"] is True,
        "historical tree not preserved",
    )
    if repository is None:
        return False
    repository = repository.resolve()
    prefix = "deployment/brain/evidence/2026-11-05/m5-free-qualification"

    def git_tree(reference):
        output = subprocess.check_output(
            ["git", "-C", str(repository), "ls-tree", "-r", reference, "--", prefix],
            text=True,
        )
        return {
            line.split("\t", 1)[1]: line.split("\t", 1)[0].split()[-1]
            for line in output.splitlines()
        }

    previous = git_tree(proof["baseline_pr25_head"])
    current = git_tree("HEAD")
    require(previous == current, "historical Git tree changed")
    for row in files:
        require(
            sha256(member(repository, row["path"])) == row["sha256"],
            "historical file hash changed",
        )
        require(
            previous[row["path"]] == current[row["path"]] == row["git_blob"],
            "historical Git blob changed",
        )
    return True


def verify(root, repository):
    checksums = load(root / "checksums.json")
    present = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "checksums.json"
    }
    require(set(checksums) == present, "published file inventory mismatch")
    for name, expected in checksums.items():
        require(
            sha256(member(root, name)) == expected, "published hash mismatch: " + name
        )
    provenance = load(root / "public-provenance.json")
    require(len(provenance["files"]) == 39, "audited source bundle count changed")
    for row in provenance["files"]:
        require(
            sha256(member(root, row["path"])) == row["public_sha256"],
            "public provenance hash mismatch",
        )
    consolidated = load(root / "qualification-consolidated.json")
    require(
        consolidated["accepted"] is False
        and consolidated["paid_pilot_admitted"] is False,
        "qualification must remain blocked",
    )
    trials = {trial["mode"]: trial for trial in consolidated["trials"]}
    require(set(trials) == {"native", "fake"}, "unexpected participant inventory")
    for mode, trial in trials.items():
        require(trial["requested_seconds"] == 1800, "requested horizon changed")
        require(
            sha256(member(root, trial["archive"])) == trial["archive_sha256"],
            "archive public hash mismatch",
        )
        events = verify_archive(member(root, trial["archive"]), trial)
        require(
            load(root / mode / "saved-character.json")["experience"]
            == trial["saved_xp"]
            == trial["last_sample_xp"],
            "saved XP mismatch",
        )
        require(
            trial["xp_delta"] == trial["last_sample_xp"] - trial["initial_xp"],
            "XP gain mismatch",
        )
        require(
            all(
                trial["metrics_v2"][key] == 0
                for key in (
                    "deaths",
                    "gaps",
                    "interventions",
                    "spent_nanousd",
                    "reserved_nanousd",
                )
            ),
            "zero-observed metric changed",
        )
        ledger = load(root / mode / "offline-ledger-export.json")
        require(
            ledger["authority"].startswith("offline-free-qualification-only:"),
            "ledger authority changed",
        )
        require(
            ledger["requests"] == []
            and ledger["budget"]["spent"] == ledger["budget"]["reserved"] == 0,
            "free ledger changed",
        )
        acceptance = load(root / mode / "strict-review" / "acceptance.json")
        if mode == "native":
            require(
                trial["recording_status"] == trial["stop_reason"] == "completed",
                "native outcome changed",
            )
            require(
                trial["sampled_span_seconds"] == 1800.493 and trial["xp_delta"] == 8349,
                "native results changed",
            )
            require(
                acceptance["ready_for_review"] is True and acceptance["findings"] == [],
                "native strict review changed",
            )
            cycle = load(root / mode / "external-cycle-review.json")
            require(
                cycle["ordered_hunt_phase_cycle_observed"] is True
                and cycle["purchase_confirmed"] is False,
                "native cycle interpretation changed",
            )
        else:
            require(
                trial["recording_status"] == "failed"
                and trial["stop_reason"] == "stalled",
                "fake failure erased",
            )
            require(
                trial["sampled_span_seconds"] == 1508.244 and trial["xp_delta"] == 1993,
                "fake results changed",
            )
            require(
                acceptance["ready_for_review"] is False, "fake incorrectly accepted"
            )
            require(
                [finding["code"] for finding in acceptance["findings"]]
                == ["qualification_not_completed"],
                "fake strict finding changed",
            )
            require(
                any(
                    event["id"] == 3873
                    and event["t_ms"] == 1266733
                    and event["data"].get("reason") == "return_route_unavailable"
                    for event in events
                ),
                "recorded return failure missing",
            )
    history_checked = verify_history(root, repository)
    return {
        "verified_files": len(checksums),
        "replay_events": {mode: trial["event_count"] for mode, trial in trials.items()},
        "historical_hashes_checked": 89 if history_checked else 0,
        "accepted": False,
        "paid_pilot_admitted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path)
    args = parser.parse_args()
    try:
        result = verify(Path(__file__).resolve().parent, args.repository)
    except (
        ValueError,
        KeyError,
        OSError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
    ) as error:
        parser.exit(1, "Evidence verification failed: " + str(error) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
