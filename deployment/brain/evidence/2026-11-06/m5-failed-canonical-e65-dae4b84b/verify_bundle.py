"""Verify closed failed-attempt evidence offline; no original DB or network access."""

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


def archive_events(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate archive member")
        integrity = json.loads(archive.read("integrity.json"))
        require(integrity["version"] == 1, "unsupported integrity version")
        require(
            set(integrity["sha256"]) == set(names) - {"integrity.json"},
            "archive inventory mismatch",
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
                hashlib.sha256(data).hexdigest() == expected,
                "archive member hash mismatch",
            )
            decoded[name] = json.loads(data)
    metadata = decoded.pop("run.json")
    events = [event for name in sorted(decoded) for event in decoded[name]]
    require(
        len({event["key"] for event in events}) == len(events), "duplicate event key"
    )
    require(metadata["event_count"] == len(events), "archive event count mismatch")
    return metadata, events


def verify(root):
    index = load(root / "checksums.json")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != root / "checksums.json"
    }
    require(set(index) == actual, "public inventory mismatch")
    for name, expected in index.items():
        path = root / name
        require(
            path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
            "unsafe public path",
        )
        require(sha(path) == expected, "public hash mismatch: " + name)
    source = "e65e8913becc6e5766e1fa050cbf82183e7ee69e"
    report = load(root / "summary.json")
    require(
        report["source_revision"] == source
        and report["status"] == "failed_before_game",
        "failure identity changed",
    )
    require(
        report["qualified"] is False and report["financial_final"] is False,
        "failed attempt incorrectly qualified",
    )
    require(
        report["scored_games_created"] == report["native_trials_created"] == 0
        and report["gameplay_xp_measured"] is False,
        "synthetic probe relabelled gameplay",
    )
    closed = load(root / "closed-attempt-receipt.json")
    require(
        closed["one_execute_invocation"] is True and closed["reinvocations"] == 0,
        "single invocation contract changed",
    )
    require(
        closed["game_campaign_created"] is False
        and closed["game_child_events_in_window"] == [],
        "game creation evidence changed",
    )
    require(
        closed["harness_absent"] is True and closed["remaining_harness_count"] == 0,
        "harness closure evidence changed",
    )
    require(
        closed["error_type"] == closed["ledger_export_error"] == "OperationalError",
        "original error class changed",
    )
    require(
        closed["retry_allowed"] is False
        and closed["cleanup_commands_by_collector"] == [],
        "collector performed retry or cleanup",
    )
    require(
        closed["canonical_ledger_opened_by_collector"] is False
        and closed["canonical_reservations_released_by_collector"] is False,
        "collector ledger scope changed",
    )
    provenance = load(root / "captured-inputs-provenance.json")
    require(
        provenance["captured_role_count"] == len(provenance["captured_sha256"]) == 7,
        "captured seven-input identity changed",
    )
    admission = provenance["runtime_admission"]
    approved = admission["approved_inputs_sha256"]
    require(
        provenance["approved_payload_count"] == len(approved) == 6,
        "six approved payload roles changed",
    )
    require(
        all(
            provenance["captured_sha256"][key] == value
            for key, value in approved.items()
        ),
        "captured/approved input mismatch",
    )
    go = load(root / "root-GO-projection.json")
    require(
        go["source_revision"] == source
        and go["admission_sha256"] == provenance["captured_sha256"]["admission"],
        "runtime admission not bound to historical GO",
    )
    require(
        go["reviewed_bundle_sha256"] == provenance["original_root_final_sha256"],
        "review bundle identity changed",
    )

    financial_cuts = []
    for folder in ("finance-1702-prices-kv", "finance-1708-integrity"):
        path = root / folder
        nested = load(path / "checksums.json")
        nested = nested.get("files", nested)
        require(
            all(sha(path / name) == expected for name, expected in nested.items()),
            "Finance original public bytes changed",
        )
        financial_cuts.append(load(path / "failed-execution-financial.public.json"))
    financial = financial_cuts[-1]
    require(
        financial["attempt_request_count"] == 5
        and financial["scored_game_ledger_requests"] == 0,
        "financial request scope changed",
    )
    require(financial["financial_final"] is False, "unknown liability liquidated")
    require(
        financial["attempt_known_spent_nanousd"]
        == report["known_spent_nanousd"]
        == 363100,
        "settled amount changed",
    )
    require(
        financial["attempt_unknown_reserved_nanousd"]
        == report["unknown_reserved_nanousd"]
        == 3357050,
        "unknown reservation erased",
    )
    require(
        financial["attempt_liability_nanousd"]
        == report["invocation_liability_nanousd"]
        == 3720150,
        "invocation liability changed",
    )
    require(
        financial["historical_known_spent_nanousd"]
        == report["historical_known_nanousd"]
        == 214600,
        "historical cost omitted",
    )
    require(
        financial["pilot_including_historical_liability_nanousd"]
        == report["liability_including_historical_nanousd"]
        == 3934750,
        "complete liability changed",
    )
    financial_rows = [
        request
        for provider in financial["providers"].values()
        for request in provider["requests"]
    ]
    require(len(financial_rows) == 5, "financial row count changed")
    require(
        sum(
            request["spent_nanousd"]
            for request in financial_rows
            if request["spent_nanousd"] is not None
        )
        == 363100,
        "settled rows do not sum to known total",
    )
    require(
        sum(
            request["reserved_nanousd"]
            for request in financial_rows
            if request["spent_nanousd"] is None
        )
        == 3357050,
        "unknown rows do not sum to liability",
    )
    require(
        sum(request["spent_nanousd"] is None for request in financial_rows) == 2,
        "unknown request count changed",
    )
    counts = {}
    all_reserved = set()
    for row in report["probes"]:
        provider = row["provider"]
        path = root / row["archive"]
        require(sha(path) == row["archive_sha256"], "archive public hash changed")
        metadata, events = archive_events(path)
        require(
            metadata["id"] == metadata["manifest"]["run_id"] == row["run_id"],
            "probe run identity changed",
        )
        require(
            metadata["manifest"]["synthetic"] is True
            and metadata["manifest"]["source_revision"] == "unknown",
            "original synthetic/unknown manifest relabelled",
        )
        require(
            metadata["manifest"]["configuration_sha256"] is None
            and metadata["status"] == row["recording_status_preserved"] == "failed",
            "original recording state changed",
        )
        require(
            len(events) == row["event_count"] == (19 if provider == "openai" else 16),
            "probe event count changed",
        )
        requests = [event["data"] for event in events if event["kind"] == "request"]
        reserved = {
            data["request_id"] for data in requests if data.get("phase") == "reserved"
        }
        terminal = {
            data["request_id"]
            for data in requests
            if data.get("phase") in {"finished", "failed"}
        }
        phases = {
            phase: sum(data.get("phase") == phase for data in requests)
            for phase in {data.get("phase") for data in requests}
        }
        expected_phases = (
            {"reserved": 3, "finished": 2, "failed": 1, "skipped": 2}
            if provider == "openai"
            else {"reserved": 2, "finished": 1, "skipped": 3}
        )
        require(
            phases == row["request_phase_counts"] == expected_phases,
            "request terminal/backoff evidence changed",
        )
        require(
            sorted(reserved - terminal) == row["reserved_without_recorded_terminal"],
            "missing terminal reconstructed",
        )
        finance_rows = financial["providers"][provider]["requests"]
        require(
            reserved
            == set(row["reserved_request_ids"])
            == {data["request_id"] for data in finance_rows},
            "replay/Finance request sets differ",
        )
        earlier = financial_cuts[0]["providers"][provider]["requests"]
        identity = lambda rows: {
            (data["request_id"], data["reserved_nanousd"], data["spent_nanousd"])
            for data in rows
        }
        require(
            identity(earlier) == identity(finance_rows),
            "financial values differ across preserved cuts",
        )
        representation = load(root / "recording-representation-equivalence.json")[
            "providers"
        ][provider]
        require(
            representation["f6_original_recording_sha256"]
            == load(root / provider / "probe-observations.json")[
                "original_recording_sha256"
            ],
            "f6 recording source mismatch",
        )
        require(
            representation["financial_snapshot_sha256"]
            == financial["providers"][provider]["recording_sha256"],
            "Finance snapshot source mismatch",
        )
        require(
            representation["metadata_and_all_events_equal"] is True
            and representation["source_properties_unchanged"] is True,
            "recording representations not reconciled",
        )
        logical_hash = hashlib.sha256(
            json.dumps(
                {"metadata": metadata, "events": events},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
        require(
            logical_hash == representation["canonical_logical_payload_sha256"],
            "archive does not match reconciled logical payload",
        )
        all_reserved.update(reserved)
        counts[provider] = len(events)
    require(len(all_reserved) == 5, "five distinct attempts not preserved")
    openai = load(root / "openai/original-result-projection.json")["qualification"]
    require(
        openai["accepted_for_game"] is True
        and openai["long_valid"] == 2
        and openai["causal_backoff"] == 2
        and openai["ledger_requests"] == 3,
        "narrow OpenAI probe result changed",
    )
    missing = load(root / "gemini/missing-result-receipt.json")
    require(
        missing["gemini_result_json_present"] is False
        and missing["campaign_result_is_null"] is True,
        "missing Gemini result recreated",
    )
    preservation = load(root / "originals-preservation.json")
    require(
        preservation["hashes_sizes_mtimes_modes_owners_unchanged"] is True
        and preservation["source_permissions_changed"] is False,
        "original preservation assertion changed",
    )
    require(
        preservation["canonical_ledger_read"] is False
        and preservation["canonical_ledger_written"] is False
        and preservation["docker_or_provider_calls_by_collector"] == 0,
        "collector exceeded offline scope",
    )
    validation = load(root / "validation-provenance.json")
    require(
        validation["current_actual"]["tests_passed"] == 534
        and validation["legacy_531"]["raw_logs_available"] is False
        and validation["legacy_531"]["recreated_original_receipt"] is False,
        "validation provenance rewritten",
    )
    return {
        "verified_files": len(index),
        "probe_events": counts,
        "reserved_http_attempts": len(all_reserved),
        "scored_games": 0,
        "qualified": False,
        "financial_final": False,
        "liability_including_historical_nanousd": 3934750,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        print("Evidence verification failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
