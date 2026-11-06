"""Read-only M5 evidence review; never launches a game or calls a provider."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sqlite3
import statistics
import tempfile
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

from canary_brain.recording import ReplayReader, public_data
from canary_brain.replay import import_archive, summarize

USD = 1_000_000_000
GAME_STOPS = {"deaths_limit", "stalled", "proposal_timeout"}


def percentile(values: list[int], fraction: float) -> int | None:
    return sorted(values)[math.ceil(len(values) * fraction) - 1] if values else None


def integer(value: Any) -> bool:
    return type(value) is int and value >= 0


def expected_runs(plan: dict[str, Any]) -> list[dict[str, Any]]:
    names = [p["name"] for p in plan["participants"]]
    repetitions = plan["repetitions"]
    if (
        len(set(names)) != len(names)
        or not names
        or type(repetitions) is not int
        or not 1 <= repetitions <= 50
    ):
        raise ValueError("Invalid participants/repetitions in the predeclared plan")
    explicit = plan.get("expected_runs")
    if explicit is not None:
        pairs = [(r["participant"], r["repetition"]) for r in explicit]
        expected = {
            (name, repetition) for name in names for repetition in range(repetitions)
        }
        identities = [r["run_id"] for r in explicit]
        if (
            len(pairs) != len(expected)
            or set(pairs) != expected
            or len(set(identities)) != len(identities)
        ):
            raise ValueError(
                "Explicit run IDs must rename the full participant/repetition grid without omitting or repeating attempts"
            )
        return list(explicit)
    return [
        {
            "run_id": f"{plan['name']}:{participant['name']}:{repetition}",
            "participant": participant["name"],
            "repetition": repetition,
        }
        for repetition in range(plan["repetitions"])
        for participant in plan["participants"]
    ]


def request_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requests: dict[str, dict[str, Any]] = {}
    decisions = {
        event["data"]["decision_id"]: event["data"].get("observation", {})
        for event in events
        if event["kind"] == "decision"
        and event["data"].get("phase") == "requested"
        and "decision_id" in event["data"]
    }
    for event in events:
        if event["kind"] != "request":
            continue
        data = event["data"]
        identity = data["request_id"]
        row = requests.setdefault(identity, {"request_id": identity})
        if data.get("phase") == "reserved":
            row["original_reservation_nanousd"] = data["reserved_nanousd"]
        row.update(data)
    for row in requests.values():
        observation = decisions.get(row.get("decision_id", ""), {})
        actions = observation.get("actions", [])
        row["offered_ttl_ms"] = min((a["ttl_ms"] for a in actions), default=None)
        row["action_classes"] = sorted({a["action"] for a in actions})
    return list(requests.values())


def latency_metrics(
    events: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    *,
    backoff_classified: bool = False,
    backoff_requests_recorded: bool = False,
) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = str(row.get("deadline_ms", "unknown"))
        groups[key].append(row)
    by_deadline = {}
    for deadline, members in sorted(groups.items()):
        attempts = [r for r in members if r.get("phase") != "skipped"]
        skipped = [
            r
            for r in members
            if r.get("phase") == "skipped" and r.get("reason") == "backoff"
        ]
        finished = [
            int(r["elapsed_ms"]) for r in members if r.get("phase") == "finished"
        ]
        failures = Counter(
            r.get("error", "unknown") for r in members if r.get("phase") == "failed"
        )
        by_deadline[deadline] = {
            "reserved_attempts": len(attempts),
            "backoff_skips_observed": len(skipped),
            "completed_responses": len(finished),
            "timeouts": failures.get("TimeoutError", 0),
            "failures_by_type": dict(failures),
            "timeout_rate": failures.get("TimeoutError", 0) / len(attempts)
            if attempts
            else None,
            "completed_p50_ms": statistics.median(finished) if finished else None,
            "completed_p95_ms": percentile(finished, 0.95),
            "completed_p95_is_deadline_censored": True,
            "offered_ttl_ms": sorted(
                {
                    r["offered_ttl_ms"]
                    for r in members
                    if r["offered_ttl_ms"] is not None
                }
            ),
            "action_classes": sorted({a for r in members for a in r["action_classes"]}),
        }
    fallbacks = Counter(
        event["data"].get("reason", "unknown")
        for event in events
        if event["kind"] == "lifecycle"
        and event["data"].get("phase") == "native_fallback"
    )
    return {
        "by_deadline_ms": by_deadline,
        "native_fallback_events_by_type": dict(fallbacks),
        "exact_backoff_skips": sum(
            g["backoff_skips_observed"] for g in by_deadline.values()
        )
        if backoff_requests_recorded
        else fallbacks.get("ProviderBackoff", 0)
        if backoff_classified
        else None,
        "observed_provider_backoff_events": fallbacks.get("ProviderBackoff", 0),
        "backoff_by_deadline_ms": {
            k: g["backoff_skips_observed"] for k, g in by_deadline.items()
        }
        if backoff_requests_recorded
        else None,
        "runtime_error_fallbacks_unclassified": fallbacks.get("RuntimeError", 0),
        "backoff_limitation": "ProviderBackoff is distinct when declared by the instrumented source. Generic RuntimeError remains ambiguous; lifecycle events without decision/deadline identity cannot establish TTL attribution.",
    }


def priced_usage(row: dict[str, Any], prices: dict[str, Any]) -> int | None:
    usage = row.get("usage", {})
    details = usage.get("input_tokens_details") or {}
    inputs, outputs = usage.get("input_tokens"), usage.get("output_tokens")
    cached, written = (
        details.get("cached_tokens", 0),
        details.get("cache_write_tokens", 0),
    )
    values = (inputs, outputs, cached, written)
    if not all(integer(v) for v in values) or inputs <= 0 or cached + written > inputs:
        return None
    fields = (
        "input_nanousd",
        "output_nanousd",
        "cached_nanousd",
    )
    if not all(integer(prices.get(key)) for key in fields):
        return None
    write_price = prices.get("cache_write_nanousd")
    if written and not integer(write_price):
        return None
    return int(
        (inputs - cached - written) * prices["input_nanousd"]
        + outputs * prices["output_nanousd"]
        + cached * prices["cached_nanousd"]
        + (written * write_price if written else 0)
    )


def review(
    experiment: dict[str, Any],
    recordings: list[dict[str, Any]],
    trials: list[dict[str, Any]],
    ledger: dict[str, Any],
    *,
    require_completed: bool = False,
) -> dict[str, Any]:
    plan = experiment["plan"]
    tolerance = experiment.get("horizon_tolerance_seconds", 5)
    if (
        type(tolerance) not in (int, float)
        or not math.isfinite(tolerance)
        or not 0 <= tolerance <= 5
    ):
        raise ValueError(
            "Completed-horizon tolerance must be predeclared within zero to five seconds"
        )
    maximum_seconds = plan["seconds"] + tolerance
    expected = expected_runs(plan)
    participants = {p["name"]: p for p in plan["participants"]}
    findings: list[dict[str, Any]] = []

    def flag(code: str, run_id: str | None, detail: str) -> None:
        findings.append({"code": code, "run_id": run_id, "detail": detail})

    def index_unique(
        rows: list[dict[str, Any]], field: str, code: str
    ) -> dict[str, dict[str, Any]]:
        result = {}
        for row in rows:
            key = row[field]
            if key in result:
                flag(
                    code,
                    key,
                    "Duplicate identity; evidence must not be mixed across reruns",
                )
            result[key] = row
        return result

    recorded = index_unique(recordings, "id", "duplicate_recording")
    trial_map = index_unique(trials, "run_id", "duplicate_trial")
    planned = {item["run_id"] for item in expected}
    if len(planned) != len(expected):
        flag("duplicate_plan", None, "Expected run IDs must be distinct")
    for extra in set(recorded) - planned:
        flag("unexpected_recording", extra, "Recording is not part of the frozen plan")
    for extra in set(trial_map) - planned:
        flag(
            "unexpected_trial",
            extra,
            "Retain and classify unplanned/replacement attempts instead of dropping them",
        )
    if not ledger.get("authority"):
        flag("ledger_authority_missing", None, "Identify the canonical ledger export")
    budget = ledger.get("budget", {})
    month = ledger.get("month")
    snapshot = ledger.get("snapshot_utc")
    captured = None
    try:
        if not isinstance(snapshot, str):
            raise TypeError("Missing UTC snapshot")
        captured = datetime.fromisoformat(snapshot)
        if (
            captured.utcoffset() != timedelta(0)
            or captured.tzinfo is None
            or captured.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m")
            != month
        ):
            raise ValueError("Snapshot month/UTC disagree")
    except (AttributeError, TypeError, ValueError):
        captured = None
        flag(
            "monthly_snapshot_time_invalid",
            None,
            "Need month in America/Sao_Paulo and an aware UTC snapshot_utc from the same ledger transaction",
        )
    if not all(
        integer(budget.get(k)) for k in ("cap", "spent", "reserved", "available")
    ):
        flag(
            "monthly_snapshot_missing",
            None,
            "Need canonical integer-nanodollar cap/spent/reserved/available snapshot",
        )
    elif budget["cap"] > 50 * USD or budget["available"] != max(
        0, budget["cap"] - budget["spent"] - budget["reserved"]
    ):
        flag(
            "monthly_snapshot_invalid",
            None,
            "Monthly cap cannot exceed USD50 and available must retain unknown liabilities",
        )
    elif budget["spent"] + budget["reserved"] > budget["cap"]:
        flag(
            "monthly_cap_exceeded",
            None,
            "Known monthly spend plus all unknown liabilities exceeds the authority's cap",
        )
    additional = set(experiment.get("additional_cost_run_ids", []))
    if additional & planned:
        flag(
            "additional_cost_overlap",
            None,
            "Probe and scored identities must not overlap",
        )
    unexpected = (set(recorded) | set(trial_map)) - planned - additional
    namespace_rows = (
        {
            r["run_id"]
            for r in ledger["requests"]
            if r["run_id"].startswith(plan["name"] + ":")
        }
        - planned
        - additional
    )
    unexpected |= namespace_rows
    for identity in namespace_rows:
        flag(
            "unexpected_ledger_run",
            identity,
            "Canonical ledger contains an unplanned campaign/replacement identity",
        )
    ledger_rows = [
        r
        for r in ledger["requests"]
        if r["run_id"] in planned | additional | unexpected
    ]
    for missing in additional - {r["run_id"] for r in ledger_rows}:
        flag(
            "additional_cost_missing",
            missing,
            "Declared prior probe must have a ledger record, not an assumed zero",
        )
    for row in ledger_rows:
        if (
            not integer(row.get("reserved"))
            or row["reserved"] <= 0
            or "spent" not in row
            or (row["spent"] is not None and not integer(row["spent"]))
        ):
            flag(
                "invalid_ledger_amount",
                row["run_id"],
                "Require a positive reserved bound and spent=null or nonnegative integer nanodollars",
            )
        if not isinstance(row.get("month"), str) or not re.fullmatch(
            r"\d{4}-(?:0[1-9]|1[0-2])", row["month"]
        ):
            flag(
                "invalid_ledger_month",
                row["run_id"],
                "Each canonical request must retain its original accounting month",
            )
        if "created" in row and (
            not isinstance(row["created"], (int, float))
            or isinstance(row["created"], bool)
            or not math.isfinite(row["created"])
            or row["created"] < 0
            or (captured is not None and row["created"] > captured.timestamp())
        ):
            flag(
                "ledger_row_after_snapshot",
                row["run_id"],
                "Request creation time must be valid and no later than the claimed snapshot",
            )
    selected_monthly_spent = sum(
        r["spent"]
        for r in ledger_rows
        if r.get("month") == month and integer(r.get("spent"))
    )
    selected_unknown = sum(
        r["reserved"]
        for r in ledger_rows
        if r.get("spent") is None and integer(r.get("reserved"))
    )
    if integer(budget.get("spent")) and budget["spent"] < selected_monthly_spent:
        flag(
            "monthly_spent_understates_rows",
            None,
            "Monthly snapshot cannot omit the selected month's settled canonical charges",
        )
    if integer(budget.get("reserved")) and budget["reserved"] < selected_unknown:
        flag(
            "monthly_reserved_understates_rows",
            None,
            "Monthly snapshot must retain selected unknown liabilities from every month",
        )
    ledger_map = index_unique(ledger_rows, "id", "duplicate_ledger_request")
    result_runs = []
    for item in expected:
        identity = item["run_id"]
        participant = participants[item["participant"]]
        recording = recorded.get(identity)
        trial = trial_map.get(identity)
        if recording is None or trial is None:
            flag(
                "missing_attempt_evidence",
                identity,
                "Every predeclared attempt needs a recording and trial record",
            )
            continue
        manifest = recording["manifest"]
        events = recording["events"]
        for field, value in {
            "participant": item["participant"],
            "initial_sha256": plan["expected_initial_sha256"],
            "configuration_sha256": experiment["configuration_sha256"],
            "memory_mode": plan["memory_mode"],
            "source_revision": plan["source_revision"],
            "provider": (participant.get("gateway") or {}).get(
                "provider", participant["kind"]
            ),
        }.items():
            if manifest.get(field) != value:
                flag("manifest_mismatch", identity, field)
        if recording["incomplete"] or any(e["kind"] == "gap" for e in events):
            flag(
                "recording_incomplete",
                identity,
                "Critical gaps/incomplete recording cannot pass qualification",
            )
        reason = trial.get("reason")
        status = recording["status"]
        expected_status = (
            "completed"
            if reason == "completed"
            else "budget_stop"
            if reason == "budget_stop"
            else "failed"
        )
        if status != expected_status or reason not in {
            "completed",
            "budget_stop",
            *GAME_STOPS,
        }:
            flag(
                "stop_status_mismatch",
                identity,
                "Unexpected/missing stop classification; retain interrupted/infrastructure attempts",
            )
        stops = [
            e["data"]
            for e in events
            if e["kind"] == "lifecycle"
            and e["data"].get("phase") == "run_supervisor_stop"
        ]
        if len(stops) != 1 or stops[0].get("reason") != reason:
            flag(
                "stop_evidence_mismatch",
                identity,
                "Need exactly one matching durable supervisor stop",
            )
        samples = sorted(
            (e for e in events if e["kind"] == "sample"), key=lambda e: e["t_ms"]
        )
        observed_ms = (
            samples[-1]["t_ms"] - samples[0]["t_ms"] if len(samples) >= 2 else 0
        )
        if reason == "completed":
            clocks = (trial.get("elapsed_seconds"), trial.get("observed_seconds"))
            if observed_ms < plan["seconds"] * 1000 or any(
                not isinstance(v, (int, float))
                or isinstance(v, bool)
                or not math.isfinite(v)
                or v < plan["seconds"]
                for v in clocks
            ):
                flag(
                    "horizon_short",
                    identity,
                    "Completion requires sample span and both worker clocks to reach the exact horizon",
                )
            if observed_ms > maximum_seconds * 1000 or any(
                isinstance(v, (int, float))
                and not isinstance(v, bool)
                and math.isfinite(v)
                and v > maximum_seconds
                for v in clocks
            ):
                flag(
                    "horizon_exceeded",
                    identity,
                    "Completed sample span and worker clocks exceed the predeclared horizon tolerance",
                )
        elif require_completed:
            flag(
                "qualification_not_completed",
                identity,
                "Free qualification requires reason=completed",
            )
        initial, saved = trial.get("initial_character"), trial.get("saved_character")
        canonical_initial = experiment.get("preflight", {}).get("character")
        if not isinstance(canonical_initial, dict) or not all(
            k in canonical_initial
            for k in ("id", "level", "experience", "posx", "posy", "posz")
        ):
            flag(
                "canonical_initial_missing",
                identity,
                "Need the complete restored character declared by preflight",
            )
        elif not isinstance(initial, dict) or any(
            initial.get(k) != value for k, value in canonical_initial.items()
        ):
            flag(
                "initial_fixture_mismatch",
                identity,
                "Restored initial character differs from the common preflight character",
            )
        if not isinstance(initial, dict) or not isinstance(saved, dict) or not samples:
            flag(
                "character_evidence_missing",
                identity,
                "Need restored initial and final saved character evidence plus samples",
            )
        else:
            for character, sample in ((initial, samples[0]), (saved, samples[-1])):
                bot = sample["data"]["bot"]
                if (
                    character.get("id") != bot["id"]
                    or character.get("experience") != bot["xp"]
                    or character.get("level") != bot["level"]
                ):
                    flag(
                        "saved_progress_mismatch",
                        identity,
                        "DB id/XP/level must match the corresponding boundary sample",
                    )
            if require_completed and saved.get("experience", 0) <= initial.get(
                "experience", 0
            ):
                flag(
                    "qualification_no_xp",
                    identity,
                    "Free qualification must demonstrate positive saved XP",
                )
        for field in ("game_image", "database_image"):
            if trial.get(field) != plan[field] or not re.fullmatch(
                r"(?:[^@\s]+@)?sha256:[a-f0-9]{64}", str(plan[field])
            ):
                flag("image_identity_mismatch", identity, field)
        if trial.get("images_verified") is not True:
            flag(
                "image_attestation_missing",
                identity,
                "Compose declarations alone do not attest the images actually used",
            )
        if trial.get("resources_cleaned") is not True:
            flag(
                "cleanup_unverified",
                identity,
                "Temporary server/database resources must be confirmed removed",
            )
        all_rows = request_rows(events)
        skipped_rows = [
            r
            for r in all_rows
            if r.get("phase") == "skipped" and r.get("reason") == "backoff"
        ]
        for skipped in skipped_rows:
            if (
                "original_reservation_nanousd" in skipped
                or skipped.get("reserved_nanousd") != 0
            ):
                flag(
                    "funded_backoff_skip",
                    identity,
                    "Skipped backoff must precede reservation and carry zero liability",
                )
        rows = [r for r in all_rows if r not in skipped_rows]
        ids = {r["request_id"] for r in rows}
        local_ledger = {
            key: r for key, r in ledger_map.items() if r["run_id"] == identity
        }
        if ids != set(local_ledger):
            flag(
                "request_ledger_set_mismatch",
                identity,
                "Replay and canonical ledger attempt sets differ",
            )
        spent = sum(
            r["spent"] for r in local_ledger.values() if integer(r.get("spent"))
        )
        reserved = sum(
            r["reserved"]
            for r in local_ledger.values()
            if r.get("spent") is None and integer(r.get("reserved"))
        )
        for row in rows:
            financial = local_ledger.get(row["request_id"])
            if financial is None:
                continue
            if not integer(financial.get("reserved")) or financial[
                "reserved"
            ] != row.get("original_reservation_nanousd"):
                flag("reservation_mismatch", identity, row["request_id"])
            cost = financial.get("spent")
            if cost is None:
                if (
                    row.get("reserved_nanousd") != financial["reserved"]
                    or row.get("phase") != "failed"
                ):
                    flag("unknown_liability_mismatch", identity, row["request_id"])
            elif (
                not integer(cost)
                or cost != row.get("spent_nanousd")
                or row.get("reserved_nanousd") != 0
            ):
                flag("settlement_mismatch", identity, row["request_id"])
            else:
                gateway = participant.get("gateway") or {}
                if priced_usage(row, gateway.get("prices", {})) != cost:
                    flag("usage_price_mismatch", identity, row["request_id"])
                if row.get("pricing_version") != gateway.get("prices", {}).get(
                    "version"
                ):
                    flag("pricing_version_mismatch", identity, row["request_id"])
                observed = row.get("gateway", {})
                if observed.get("deployment_id") != gateway.get("deployment_id"):
                    flag("deployment_mismatch", identity, row["request_id"])
                if row.get("effective_model") != gateway.get("effective_model"):
                    flag("model_mismatch", identity, row["request_id"])
        if participant["kind"] in {"native", "fake"} and (rows or local_ledger):
            flag(
                "free_participant_inference",
                identity,
                "Native/fake participants must have no billable requests",
            )
        if (
            participant["kind"] == "litellm"
            and spent + reserved > plan["run_cap_nanousd"]
        ):
            flag(
                "run_cap_exceeded",
                identity,
                "Settled plus unknown liabilities exceed the predeclared run cap",
            )
        metrics = summarize(events, manifest)
        if not metrics["deaths_observed"]:
            flag(
                "death_telemetry_missing",
                identity,
                "Death/survival evidence is unavailable, not zero",
            )
        result_runs.append(
            {
                "run_id": identity,
                "participant": item["participant"],
                "repetition": item["repetition"],
                "status": status,
                "stop_reason": reason,
                "observed_span_ms": observed_ms,
                "metrics": metrics,
                "ledger_spent_nanousd": spent,
                "ledger_unknown_nanousd": reserved,
                "xp_per_settled_dollar": metrics["xp_delta"] * USD / spent
                if spent and not reserved and metrics["xp_delta"] is not None
                else None,
                "requests": rows,
                "skipped_requests": skipped_rows,
                "latency": latency_metrics(
                    events,
                    all_rows,
                    backoff_classified=experiment.get("instrumentation", {}).get(
                        "provider_backoff_classification"
                    )
                    == "ProviderBackoff",
                    backoff_requests_recorded=experiment.get("instrumentation", {}).get(
                        "request_backoff_events"
                    )
                    is True,
                ),
            }
        )
    # The ledger remains authoritative even when replay/trial evidence is missing.
    total_spent = sum(r["spent"] for r in ledger_rows if integer(r.get("spent")))
    total_unknown = sum(
        r["reserved"]
        for r in ledger_rows
        if r.get("spent") is None and integer(r.get("reserved"))
    )
    total_cap = experiment.get("total_cap_nanousd", plan["campaign_cap_nanousd"])
    if additional and "total_cap_nanousd" not in experiment:
        flag(
            "total_envelope_missing",
            None,
            "Predeclare a total ceiling including probes",
        )
    if total_spent + total_unknown > total_cap:
        flag(
            "campaign_cap_exceeded",
            None,
            "Settled plus unknown charges exceed the campaign ceiling",
        )
    distributions = []
    for participant in participants:
        members = [r for r in result_runs if r["participant"] == participant]
        values = [
            r["metrics"]["xp_per_wall_hour"]
            for r in members
            if r["metrics"]["xp_per_wall_hour"] is not None
        ]
        distributions.append(
            {
                "participant": participant,
                "attempts": len(members),
                "completed": sum(r["status"] == "completed" for r in members),
                "xp_per_wall_hour_values": values,
                "xp_per_wall_hour_median": statistics.median(values)
                if values
                else None,
                "xp_per_wall_hour_min": min(values) if values else None,
                "xp_per_wall_hour_max": max(values) if values else None,
            }
        )
    return {
        "schema_version": 1,
        "campaign": plan["name"],
        "horizon_seconds": plan["seconds"],
        "horizon_tolerance_seconds": tolerance,
        "maximum_completed_seconds": maximum_seconds,
        "ready_for_review": not findings,
        "financial_totals_complete": not any(
            f["code"]
            in {
                "additional_cost_missing",
                "invalid_ledger_amount",
                "duplicate_ledger_request",
                "request_ledger_set_mismatch",
                "ledger_authority_missing",
                "monthly_snapshot_missing",
                "monthly_snapshot_invalid",
                "monthly_snapshot_time_invalid",
                "invalid_ledger_month",
                "monthly_spent_understates_rows",
                "monthly_reserved_understates_rows",
                "ledger_row_after_snapshot",
            }
            for f in findings
        ),
        "expected_attempts": len(expected),
        "recorded_attempts": len(recorded),
        "reviewed_attempts": len(result_runs),
        "settled_nanousd": total_spent,
        "unknown_nanousd": total_unknown,
        "additional_cost_run_ids": sorted(additional),
        "unplanned_cost_run_ids": sorted(unexpected),
        "unplanned_spent_nanousd": sum(
            r["spent"]
            for r in ledger_rows
            if r["run_id"] in unexpected and integer(r.get("spent"))
        ),
        "unplanned_unknown_nanousd": sum(
            r["reserved"]
            for r in ledger_rows
            if r["run_id"] in unexpected
            and r.get("spent") is None
            and integer(r.get("reserved"))
        ),
        "ledger_snapshot_month": month,
        "ledger_snapshot_utc": snapshot,
        "total_cap_nanousd": total_cap,
        "monthly_snapshot": {
            key: budget.get(key) if integer(budget.get(key)) else None
            for key in ("cap", "spent", "reserved", "available")
        },
        "runs": result_runs,
        "participants": distributions,
        "findings": findings,
        "verdict": "descriptive_pilot_no_winner",
        "limitations": [
            "The independent run is the sample unit; repeated frames are not extra samples.",
            "Completed-response latency is deadline-censored; inspect failures by deadline.",
            "Generic RuntimeError fallback is not an exact backoff count; instrumented ProviderBackoff is reported separately. TTL attribution requires additional identity.",
            "Usage-priced costs are not provider invoice reconciliation.",
            "This checker does not establish fixture hunt/resupply acceptance or human/AFK safety.",
        ],
    }


def load_recordings(paths: list[Path]) -> list[dict[str, Any]]:
    result = []
    for path in paths:
        if not path.is_file() or path.is_symlink():
            raise ValueError(
                "Recording must be an existing nonsymlink SQLite or replay ZIP"
            )
        with tempfile.TemporaryDirectory(prefix="m5-report-import-") as directory:
            source = path
            if zipfile.is_zipfile(path):
                source = Path(directory) / "recording.sqlite3"
                import_archive(path, source)
            else:
                source = sqlite_copy(path, Path(directory))
            with ReplayReader(source).snapshot() as reader:
                for metadata in reader.runs(limit=100):
                    result.append(
                        {**metadata, "events": list(reader.all_events(metadata["id"]))}
                    )
    return result


def sqlite_copy(source: Path, directory: Path) -> Path:
    """SQLite read-only opens may create sidecars; open only private copies."""
    destination = directory / "snapshot.sqlite3"
    shutil.copyfile(source, destination)
    wal = Path(str(source) + "-wal")
    if wal.is_file():
        shutil.copyfile(wal, Path(str(destination) + "-wal"))
    return destination


def input_hashes(paths: list[Path]) -> dict[str, str]:
    result = {}
    for path in paths:
        for candidate in (path, Path(str(path) + "-wal")):
            if candidate.is_file():
                result[str(candidate)] = hashlib.sha256(
                    candidate.read_bytes()
                ).hexdigest()
    return result


def trials_from_root(
    directory: Path, experiment: dict[str, Any], attestation: dict[str, Any]
) -> list[dict[str, Any]]:
    result = []
    for item in expected_runs(experiment["plan"]):
        folder = directory / f"{item['participant']}-{item['repetition']}"
        trial: dict[str, Any] = {"run_id": item["run_id"]}
        state = folder / "worker.sqlite3"
        if state.is_file():
            with tempfile.TemporaryDirectory(prefix="m5-report-state-") as temporary:
                snapshot = sqlite_copy(state, Path(temporary))
                uri = "file:" + quote(str(snapshot), safe="/") + "?mode=ro"
                with sqlite3.connect(uri, uri=True) as db:
                    row = db.execute(
                        "SELECT data FROM records WHERE kind='run_stop' AND key='end'"
                    ).fetchone()
            trial.update(json.loads(row[0]) if row else {})
        saved = folder / "saved-character.json"
        if saved.is_file():
            trial["saved_character"] = json.loads(saved.read_text())
        trial["initial_character"] = experiment.get("preflight", {}).get("character")
        per_run = attestation.get("trials", {}).get(item["run_id"], attestation)
        for field in (
            "game_image",
            "database_image",
            "images_verified",
            "resources_cleaned",
        ):
            trial[field] = per_run.get(field)
        result.append(trial)
    return result


def markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# M5 evidence report: {report['campaign']}",
        "",
        f"Ready for review: {report['ready_for_review']}. Verdict: descriptive pilot, no winner.",
        f"Financial totals complete: {report['financial_totals_complete']}; if false, displayed values are only known valid amounts, not a complete cost/passive total.",
        "",
        "| Run | Status/reason | Observed seconds | XP | Deaths | Interventions | Settled USD | Unknown USD |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["runs"]:
        m = row["metrics"]
        lines.append(
            f"| {row['run_id']} | {row['status']}/{row['stop_reason']} | {row['observed_span_ms'] / 1000:.3f} | {m['xp_delta']} | {m['deaths']} | {m['interventions']} | {row['ledger_spent_nanousd'] / USD:.9f} | {row['ledger_unknown_nanousd'] / USD:.9f} |"
        )
    lines += ["", "## Findings", ""]
    lines.extend(
        f"- {f['code']} ({f['run_id']}): {f['detail']}" for f in report["findings"]
    )
    if not report["findings"]:
        lines.append(
            "No evidence-consistency findings. This does not close the issue automatically."
        )
    lines += [
        "",
        "## Interpretation",
        "",
        *["- " + v for v in report["limitations"]],
        "",
        "Per-request usage, TTL/deadline slices, classified timeouts and distributions are in report.json.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recording", type=Path, action="append", required=True)
    parser.add_argument("--experiment", type=Path, required=True)
    trials = parser.add_mutually_exclusive_group(required=True)
    trials.add_argument("--trials", type=Path)
    trials.add_argument("--trials-root", type=Path)
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-completed", action="store_true")
    args = parser.parse_args()
    inputs = [
        *args.recording,
        args.experiment,
        args.ledger,
        *([args.trials] if args.trials else []),
        *([args.attestation] if args.attestation else []),
    ]
    base_inputs = list(inputs)
    base_hashes = input_hashes(base_inputs)
    experiment = json.loads(args.experiment.read_text())
    if args.trials_root:
        for item in expected_runs(experiment["plan"]):
            folder = args.trials_root / f"{item['participant']}-{item['repetition']}"
            inputs.extend((folder / "worker.sqlite3", folder / "saved-character.json"))
    hashes = input_hashes(inputs)
    if base_hashes != input_hashes(base_inputs):
        raise ValueError("Inputs changed while loading the experiment")
    trials_data = (
        json.loads(args.trials.read_text())["trials"]
        if args.trials
        else trials_from_root(
            args.trials_root,
            experiment,
            json.loads(args.attestation.read_text()) if args.attestation else {},
        )
    )
    report = review(
        experiment,
        load_recordings(args.recording),
        trials_data,
        json.loads(args.ledger.read_text()),
        require_completed=args.require_completed,
    )
    if hashes != input_hashes(inputs):
        raise ValueError(
            "Inputs changed during review; export a stable evidence snapshot"
        )
    report["input_sha256"] = hashes
    report = public_data(report)
    # New output identity prevents mixed artifacts from interrupted reruns.
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    for name, data in (
        ("report.json", report),
        (
            "acceptance.json",
            {
                key: report[key]
                for key in (
                    "ready_for_review",
                    "financial_totals_complete",
                    "findings",
                    "verdict",
                )
            },
        ),
    ):
        (args.output / name).write_text(
            json.dumps(data, indent=2, allow_nan=False) + "\n"
        )
    (args.output / "report.md").write_text(markdown(report))
    print(
        json.dumps(
            {
                "output": str(args.output),
                "ready_for_review": report["ready_for_review"],
                "findings": len(report["findings"]),
            }
        )
    )
    if not report["ready_for_review"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
