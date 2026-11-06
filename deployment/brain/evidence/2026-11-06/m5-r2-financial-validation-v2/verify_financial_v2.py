"""Read-only financial cross-check of the published R2 negative qualification."""

import argparse
import hashlib
import json
import runpy
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "m5-r2-negative-qualification-27120d96"
V1_SHA256 = "49c353d7f3d2d92d3e198c2fec80c707808e669f98977561549a6fd60039e4bc"
PARENT_INDEX_SHA256 = "c507e4e033a8c3bd2942ecdd58a38eed7c6c9097e5d191fa27d1525354822c6b"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_supplement():
    index = load(HERE / "checksums.json")
    files = {
        path.relative_to(HERE).as_posix()
        for path in HERE.rglob("*")
        if path.is_file() and path != HERE / "checksums.json"
    }
    require(set(index) == files, "supplement inventory changed")
    for name, expected in index.items():
        path = HERE / name
        require(
            path.resolve().is_relative_to(HERE) and not path.is_symlink(),
            "unsafe supplement path",
        )
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == expected,
            "supplement hash changed: " + name,
        )
    manifest = load(HERE / "supplement-manifest.json")
    require(
        manifest["parent_checksums_sha256"]
        == hashlib.sha256((PARENT / "checksums.json").read_bytes()).hexdigest()
        == PARENT_INDEX_SHA256,
        "original parent index changed",
    )
    require(
        manifest["parent_v1_checker_sha256"] == V1_SHA256, "V1 manifest pin differs"
    )


def money(value, label):
    require(type(value) is int and value >= 0, label + " must be a nonnegative integer")
    return value


def equals_money(actual, expected, label):
    require(money(actual, label) == expected, label + " does not reconcile")


def v1_verify(root):
    """Use the pinned published checker, never code supplied by --parent."""
    checker = PARENT / "verify_bundle.py"
    require(
        hashlib.sha256(checker.read_bytes()).hexdigest() == V1_SHA256,
        "published V1 checker changed",
    )
    return runpy.run_path(str(checker), run_name="r2_evidence_v1")["verify"](root)


def request_events(root):
    with zipfile.ZipFile(root / "openai-r2-decisions.replay.zip") as archive:
        metadata = json.loads(archive.read("run.json"))
        events = [
            event["data"]
            for name in sorted(archive.namelist())
            if name not in {"run.json", "integrity.json"}
            for event in json.loads(archive.read(name))
            if event["kind"] == "request"
        ]
    return metadata, events


def priced_usage(event, prices):
    usage = event["usage"]
    inputs = money(usage["input_tokens"], "usage input tokens")
    outputs = money(usage["output_tokens"], "usage output tokens")
    details = usage["input_tokens_details"]
    cached = money(details["cached_tokens"], "usage cached tokens")
    written = money(details["cache_write_tokens"], "usage cache-write tokens")
    reasoning = money(
        usage["output_tokens_details"]["reasoning_tokens"], "usage reasoning tokens"
    )
    require(cached + written <= inputs, "cached/write tokens exceed input")
    require(reasoning <= outputs, "reasoning tokens exceed output")
    equals_money(usage["total_tokens"], inputs + outputs, "usage total tokens")
    require(event["pricing_version"] == prices["version"], "pricing version differs")
    # Reasoning is included in output_tokens; do not bill it a second time.
    return (
        (inputs - cached - written) * money(prices["input_nanousd"], "input price")
        + cached * money(prices["cached_nanousd"], "cached price")
        + written * money(prices["cache_write_nanousd"], "cache-write price")
        + outputs * money(prices["output_nanousd"], "output price")
    )


def totals(rows):
    known = sum(row["spent"] for row in rows if row["spent"] is not None)
    unknown = sum(row["reserved"] for row in rows if row["spent"] is None)
    return known, unknown, known + unknown


def verify(root=PARENT):
    baseline = v1_verify(root)
    report = load(root / "summary.json")
    ledger = load(root / "closed-executor-ledger-projection.json")
    finance = load(root / "finance-1821/r2-postclosure-financial.public.json")
    provenance = load(root / "input-and-source-provenance.json")
    metadata, events = request_events(root)
    for label, header in (
        ("closed monthly header", ledger["budget"]),
        ("Finance monthly header", finance["canonical_budget_nanousd"]),
    ):
        for name in ("cap", "spent", "reserved", "available"):
            money(header[name], label + " " + name)
        require(
            header["cap"] == header["spent"] + header["reserved"] + header["available"],
            label + " does not reconcile at its own cutoff",
        )
    rows = ledger["requests"]
    by_id = {row["id"]: row for row in rows}
    for row in rows:
        require(isinstance(row["id"], str) and row["id"], "invalid request ID")
        require(isinstance(row["run_id"], str) and row["run_id"], "invalid run ID")
        require(
            row["month"] == ledger["month"] == finance["month"], "row month differs"
        )
        require(money(row["reserved"], "ledger reserved") > 0, "empty reservation")
        if row["spent"] is not None:
            money(row["spent"], "ledger spent")
            require(
                row["spent"] <= row["reserved"], "settled spend exceeds reservation"
            )

    grouped = {}
    skipped = set()
    for event in events:
        request_id = event["request_id"]
        money(event["reserved_nanousd"], "event reserved")
        if event["phase"] == "skipped":
            require(
                event["reserved_nanousd"] == 0 and request_id not in by_id,
                "local backoff became a ledger reservation",
            )
            skipped.add(request_id)
            continue
        phases = grouped.setdefault(request_id, {})
        require(event["phase"] not in phases, "duplicate request phase")
        phases[event["phase"]] = event
    new_ids = set(grouped)
    require(not (skipped & new_ids), "backoff shares a billed request ID")
    finance_rows = finance["new_requests"]
    finance_by_id = {row["request_id"]: row for row in finance_rows}
    require(
        len(finance_rows) == len(finance_by_id) == 3 and set(finance_by_id) == new_ids,
        "Finance new request identity differs",
    )
    require(
        metadata["id"] == finance["new_openai_run_id"], "Finance replay run ID differs"
    )
    prices = provenance["probe_routes"]["openai"]["prices"]
    for request_id, phases in grouped.items():
        row = by_id[request_id]
        financial = finance_by_id[request_id]
        require(row["run_id"] == metadata["id"], "new ledger run ID differs")
        require(
            set(phases) in ({"reserved", "finished"}, {"reserved", "failed"}),
            "new request must have one reservation and one terminal event",
        )
        reserved = phases["reserved"]
        equals_money(
            reserved["reserved_nanousd"], row["reserved"], "replay reservation"
        )
        equals_money(
            financial["reserved_nanousd"], row["reserved"], "Finance reservation"
        )
        if "finished" in phases:
            finished = phases["finished"]
            require(
                row["spent"] is not None, "finished request has unknown ledger spend"
            )
            equals_money(
                finished["reserved_nanousd"], 0, "finished reservation remainder"
            )
            equals_money(
                finished["spent_nanousd"], row["spent"], "replay settled spend"
            )
            equals_money(
                financial["spent_nanousd"], row["spent"], "Finance settled spend"
            )
            equals_money(
                row["spent"], priced_usage(finished, prices), "usage-priced spend"
            )
            require(financial["state"] == "settled", "Finance settled state differs")
            terminal = finished
        else:
            terminal = phases["failed"]
            require(
                row["spent"] is None
                and financial["spent_nanousd"] is None
                and financial["state"] == "unknown"
                and terminal["unsettled"] is True,
                "failed request lost its unknown liability",
            )
            equals_money(
                terminal["reserved_nanousd"],
                row["reserved"],
                "failed retained reservation",
            )
            require(
                "spent_nanousd" not in terminal, "failed request forged settled spend"
            )
        require(
            terminal["decision_id"] == reserved["decision_id"],
            "request terminal linked to another decision",
        )

    new = [row for row in rows if row["id"] in new_ids]
    prior = [row for row in rows if row["id"] not in new_ids]
    historical = [
        row for row in prior if row["run_id"].startswith("credential-smoke-out-")
    ]
    new_known, new_unknown, new_liability = totals(new)
    prior_known, prior_unknown, prior_liability = totals(prior)
    known, unknown, liability = totals(rows)
    expected_summary = {
        "known_new_spent_nanousd": new_known,
        "unknown_new_reserved_nanousd": new_unknown,
        "new_liability_nanousd": new_liability,
        "prior_liability_nanousd": prior_liability,
        "cumulative_known_spent_nanousd": known,
        "cumulative_unknown_reserved_nanousd": unknown,
        "cumulative_liability_nanousd": liability,
    }
    for name, expected in expected_summary.items():
        equals_money(report[name], expected, "summary " + name)
    expected_finance = {
        "prior_application_attempts": len(prior),
        "prior_complete_liability_nanousd": prior_liability,
        "historical_requests": len(historical),
        "historical_known_spent_nanousd": totals(historical)[0],
        "new_openai_reserved_application_attempts": len(new),
        "new_known_spent_nanousd": new_known,
        "new_unknown_reserved_nanousd": new_unknown,
        "new_complete_liability_nanousd": new_liability,
        "cumulative_complete_liability_nanousd": liability,
    }
    for name, expected in expected_finance.items():
        equals_money(finance[name], expected, "Finance " + name)
    equals_money(finance["recovery_claim"]["count"], 1, "claim count")
    equals_money(
        report["openai_reserved_application_attempts"], len(new), "summary attempts"
    )
    require(
        (known, unknown, liability)
        == (
            new_known + prior_known,
            new_unknown + prior_unknown,
            new_liability + prior_liability,
        ),
        "prior/new partition differs",
    )
    return {
        **baseline,
        "financial_validator_version": 2,
        "known_new_spent_nanousd": new_known,
        "unknown_new_reserved_nanousd": new_unknown,
        "prior_known_spent_nanousd": prior_known,
        "prior_unknown_reserved_nanousd": prior_unknown,
        "cumulative_known_spent_nanousd": known,
        "cumulative_unknown_reserved_nanousd": unknown,
        "per_request_usage_pricing_verified": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--parent", type=Path, default=PARENT, help="public appendix copy"
    )
    args = parser.parse_args()
    try:
        verify_supplement()
        print(json.dumps(verify(args.parent), sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as error:
        print("Financial verification failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
