"""Verify this closed partial-evidence append using files only; no SQLite/API."""

import hashlib
import json
import sys
import zipfile
from pathlib import Path

FINANCE_SHA = "3b956b89a2b93a53c0d8f483df140b56faad9687904cb5235cb5f5758b7397dd"
SOURCE = "7f2904e5827edc67997d309d453fa1d7371523cc"


def require(value, message):
    if not value:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def amount(value):
    require(type(value) is int and value >= 0, "invalid monetary integer")
    return value


def usage_cost(event, prices):
    usage = event["usage"]
    inputs, outputs = amount(usage["input_tokens"]), amount(usage["output_tokens"])
    details = usage["input_tokens_details"]
    cached, written = (
        amount(details.get("cached_tokens", 0)),
        amount(details.get("cache_write_tokens", 0)),
    )
    require(cached + written <= inputs, "invalid cached input counts")
    require(usage["total_tokens"] == inputs + outputs, "usage token total differs")
    write_price = amount(prices["cache_write_nanousd"]) if written else 0
    require(event["pricing_version"] == prices["version"], "price version differs")
    return (
        (inputs - cached - written) * amount(prices["input_nanousd"])
        + cached * amount(prices["cached_nanousd"])
        + written * write_price
        + outputs * amount(prices["output_nanousd"])
    )


def archive_data(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate archive member")
        require(
            all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in names),
            "unsafe archive name",
        )
        integrity = json.loads(archive.read("integrity.json"))
        require(
            set(integrity["sha256"]) == set(names) - {"integrity.json"},
            "archive inventory differs",
        )
        for name, expected in integrity["sha256"].items():
            require(
                hashlib.sha256(archive.read(name)).hexdigest() == expected,
                "archive hash differs",
            )
        meta = json.loads(archive.read("run.json"))
        events = [
            e
            for n in sorted(names)
            if n not in {"run.json", "integrity.json"}
            for e in json.loads(archive.read(n))
        ]
    require(meta["event_count"] == len(events), "archive event count differs")
    return meta, events


def verify(root):
    index = load(root / "checksums.json")
    files = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and p != root / "checksums.json"
    }
    require(set(index) == files, "public inventory differs")
    for name, expected in index.items():
        path = root / name
        require(
            path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
            "unsafe public path",
        )
        require(sha(path) == expected, "public hash differs: " + name)
    summary = load(root / "summary.json")
    report = load(root / "report/report.json")
    closure = load(root / "closure-projection.json")
    provenance = load(root / "input-and-source-provenance.json")
    require(
        summary["source_revision"] == provenance["source_revision"] == SOURCE,
        "producer differs",
    )
    require(
        summary["comparative_pilot_completed"] is False
        and summary["completed_game_runs"] == 0
        and summary["ai_game_runs_started"] == 0
        and summary["partial_native_runs"] == 1,
        "partial campaign forged as completed/AI gameplay",
    )
    require(
        len(summary["expected_runs"]) == 9
        and len(summary["not_started_reported_by_owner"]) == 8
        and summary["not_started_gameplay_metrics"] is None,
        "missing games forged as observations",
    )
    require(
        (
            report["expected_attempts"],
            report["recorded_attempts"],
            report["reviewed_attempts"],
        )
        == (9, 1, 1)
        and report["ready_for_review"] is False
        and len(report["findings"]) == 12,
        "canonical reporter findings erased",
    )
    require(
        sum(f["code"] == "missing_attempt_evidence" for f in report["findings"]) == 8,
        "eight missing attempts erased",
    )
    require(
        closure["execution_exit_code"] == 1
        and closure["campaign_result"]["campaign"] is None
        and closure["remaining_eight_not_started_reported_by_owner"] is True,
        "closed invocation scope differs",
    )
    require(
        len(closure["exact_projects_after_close"]) == 9
        and all(
            p["containers"] == p["networks"] == []
            for p in closure["exact_projects_after_close"]
        )
        and closure["native_trial"]["resources_cleaned"] is True
        and closure["native_trial"]["images_verified"] is True,
        "cleanup/actual image evidence differs",
    )
    require(
        summary["financial_final"] is report["financial_final"] is False
        and report["financial_totals_complete"] is True,
        "unknown liability finalized or totals changed",
    )
    financial_path = root / "finance-2000/none-v3-postclosure-financial.public.json"
    require(
        sha(financial_path) == FINANCE_SHA, "original final Finance receipt changed"
    )
    finance = load(financial_path)
    rows = load(root / "closed-executor-ledger.json")["requests"]
    by_id = {r["id"]: r for r in rows}
    financial = {r["request_id"]: r for r in finance["selected_requests"]}
    require(
        len(rows) == len(by_id) == len(financial) == 18
        and set(by_id) == set(financial),
        "eighteen financial identities differ",
    )
    for key, row in by_id.items():
        other = financial[key]
        amount(row["reserved"])
        if row["spent"] is not None:
            amount(row["spent"])
        require(
            (row["run_id"], row["reserved"], row["spent"])
            == (other["run_id"], other["reserved_nanousd"], other["spent_nanousd"]),
            "per-request Finance mismatch",
        )
    known = sum(r["spent"] for r in rows if r["spent"] is not None)
    unknown = sum(r["reserved"] for r in rows if r["spent"] is None)
    require((known, unknown) == (1981700, 5245675), "known/unknown liability differs")
    require(
        (
            amount(summary["known_spent_nanousd"]),
            amount(summary["unknown_reserved_nanousd"]),
            amount(summary["complete_liability_nanousd"]),
        )
        == (known, unknown, known + unknown),
        "summary financial partition differs",
    )
    require(
        (report["settled_nanousd"], report["unknown_nanousd"]) == (known, unknown),
        "report financial totals differ",
    )
    require(
        not any(r["run_id"].startswith(summary["campaign"] + ":") for r in rows),
        "game charges invented",
    )
    for claim in finance["claims"].values():
        require(
            type(claim["count"]) is int
            and claim["count"] == 1
            and claim["not_a_billable_request"] is True,
            "consumed nonbillable claim reclassified",
        )
    require(
        len(list((root / "replays").glob("*.zip"))) == 3,
        "unavailable game archives fabricated",
    )
    native, events = archive_data(root / "replays/native-partial.replay.zip")
    gaps = [e for e in events if e["kind"] == "gap"]
    samples = [e for e in events if e["kind"] == "sample"]
    require(
        native["status"] == "failed"
        and native["incomplete"] is True
        and native["manifest"]["source_revision"] == SOURCE
        and len(events) == 411,
        "native incomplete history relabelled",
    )
    require(
        len(gaps) == 1
        and gaps[0]["data"] == {"missing": 1, "reason": "native_telemetry_loss"}
        and len(samples) == 183
        and samples[-1]["t_ms"] - samples[0]["t_ms"] == 220803,
        "native critical gap/horizon changed",
    )
    require(
        not any(e["kind"] == "request" for e in events), "native AI calls fabricated"
    )
    current_ids = set()
    for provider, expected_count in [("openai", 3), ("gemini", 5)]:
        probe = load(root / (provider + "-probe-result.json"))
        require(
            probe["qualification"]["accepted_for_game"] is True
            and probe["qualification"]["evidence_reconciled"] is True,
            "real probe acceptance erased",
        )
        meta, events = archive_data(root / "replays" / (provider + "-probe.replay.zip"))
        require(
            meta["manifest"]["synthetic"] is True
            and meta["manifest"]["source_revision"] == "unknown"
            and meta["manifest"]["configuration_sha256"] is None,
            "synthetic manifest relabelled as gameplay/source",
        )
        groups = {}
        for event in events:
            if event["kind"] == "request":
                data = event["data"]
                groups.setdefault(data["request_id"], {})[data["phase"]] = data
        reserved = {
            key: phases for key, phases in groups.items() if "reserved" in phases
        }
        require(len(reserved) == expected_count, "probe attempt count changed")
        for key, phases in reserved.items():
            require(key not in current_ids, "duplicate current financial identity")
            current_ids.add(key)
            row = by_id[key]
            require(
                row["run_id"] == meta["id"]
                and row["reserved"] == amount(phases["reserved"]["reserved_nanousd"]),
                "probe reservation/run differs",
            )
            if "finished" in phases:
                finished = phases["finished"]
                require(
                    row["spent"]
                    == amount(finished["spent_nanousd"])
                    == usage_cost(
                        finished, provenance["probe_routes"][provider]["prices"]
                    ),
                    "usage-priced settlement differs",
                )
            else:
                require(
                    row["spent"] is None
                    and phases["failed"]["unsettled"] is True
                    and row["reserved"] == phases["failed"]["reserved_nanousd"],
                    "unknown probe reservation lost",
                )
        for key, phases in groups.items():
            if "skipped" in phases:
                require(
                    key not in by_id and phases["skipped"]["reserved_nanousd"] == 0,
                    "local skip became paid attempt",
                )
    require(len(current_ids) == 8, "new probe identity set differs")
    return {
        "files_verified": len(index),
        "planned_games": 9,
        "partial_games": 1,
        "not_started_reported_by_owner": 8,
        "ai_game_runs": 0,
        "replays": 3,
        "selected_financial_rows": 18,
        "known_nanousd": known,
        "unknown_nanousd": unknown,
        "financial_final": False,
        "comparative_pilot_completed": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as error:
        print("Evidence verification failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
