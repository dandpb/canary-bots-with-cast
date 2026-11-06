"""Offline check of a negative qualification appendix; no SQLite or external access."""

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
    files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != root / "checksums.json"
    }
    require(set(index) == files, "public inventory changed")
    for name, expected in index.items():
        path = root / name
        require(
            path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
            "unsafe public path",
        )
        require(sha(path) == expected, "public hash changed: " + name)
    report = load(root / "summary.json")
    closure = load(root / "closure-projection.json")
    execution = load(root / "execution-result-projection.json")
    probe = load(root / "openai-probe-result.json")
    observed = load(root / "probe-recording-observations.json")
    require(
        report["source_revision"]
        == closure["source_revision"]
        == "4c5bb9bf4b93fb11abffd7bd3020e6381296fd6d",
        "producer identity changed",
    )
    require(
        report["qualification_accepted"] is False
        and report["comparative_pilot_completed"] is False,
        "negative qualification forged as accepted",
    )
    require(
        report["gameplay_metrics"]
        == {"xp_delta": None, "deaths": None, "interventions": None},
        "unobserved gameplay forged as zero-success metrics",
    )
    require(
        report["scored_trials_started"]
        == report["native_trials_started"]
        == closure["scored_trials_started"]
        == 0,
        "game outcomes invented",
    )
    require(
        report["gemini_R2_evaluated"] is False
        and closure["gemini_R2_qualification_started"] is False,
        "unevaluated Gemini forged as tested",
    )
    require(
        execution["campaign"] is None
        and set(execution["probes"]) == {"openai"}
        and execution["ledger_export_error_present"] is False,
        "closed execution scope changed",
    )
    require(
        closure["campaign_result"] is None
        and closure["one_execute_invocation"] is True
        and closure["reinvocations"] == 0
        and closure["retry_allowed"] is False,
        "single closed invocation changed",
    )
    require(
        closure["harness_id"] is None
        and closure["harness_destroy_event_observed"] is False
        and closure["harness_absent"] is True,
        "missing harness identity/history fabricated",
    )
    require(
        len(closure["owned_project_absence"]) == 9
        and all(
            value == {"container": [], "network": []}
            for value in closure["owned_project_absence"].values()
        ),
        "owned-project absence changed",
    )
    require(
        probe["qualification"]["accepted_for_game"] is False
        and probe["qualification"]["evidence_reconciled"] is False,
        "probe rejection erased",
    )
    require(
        probe["qualification"]["technical_invalid"] == 3
        and report["financial_final"] is False,
        "original provisional result changed",
    )
    require(
        [item.get("error", item.get("choice")) for item in probe["decisions"]]
        == [
            "ValueError",
            "hunt:399",
            "resupply",
            "TimeoutError",
            "ProviderBackoff",
            "ProviderBackoff",
        ],
        "case outcomes reclassified",
    )
    archives = list(root.rglob("*.replay.zip"))
    require(
        len(archives) == 1 and archives[0].name == "openai-r2-decisions.replay.zip",
        "nonexistent Gemini/game archive added",
    )
    with zipfile.ZipFile(archives[0]) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate archive member")
        integrity = json.loads(archive.read("integrity.json"))
        require(
            integrity["version"] == 1
            and set(integrity["sha256"]) == set(names) - {"integrity.json"},
            "archive inventory changed",
        )
        decoded = {}
        for name, expected in integrity["sha256"].items():
            data = archive.read(name)
            require(
                hashlib.sha256(data).hexdigest() == expected,
                "archive integrity changed",
            )
            decoded[name] = json.loads(data)
    metadata = decoded.pop("run.json")
    events = [item for name in sorted(decoded) for item in decoded[name]]
    require(
        metadata["id"] == observed["run_id"] == metadata["manifest"]["run_id"]
        and len(events) == metadata["event_count"] == observed["event_count"] == 18,
        "replay identity/count changed",
    )
    require(
        metadata["manifest"]["synthetic"] is True
        and metadata["manifest"]["source_revision"] == "unknown"
        and metadata["manifest"]["configuration_sha256"] is None,
        "original synthetic manifest relabelled",
    )
    requests = [event["data"] for event in events if event["kind"] == "request"]
    reserved = {
        item["request_id"] for item in requests if item.get("phase") == "reserved"
    }
    require(
        len(reserved) == 3 and sorted(reserved) == observed["reserved_request_ids"],
        "three reserved attempts changed",
    )
    phases = {
        phase: sum(item.get("phase") == phase for item in requests)
        for phase in {item.get("phase") for item in requests}
    }
    require(
        phases == {"reserved": 3, "finished": 2, "failed": 1, "skipped": 2},
        "request/timeout/backoff record changed",
    )
    ledger = load(root / "closed-executor-ledger-projection.json")
    rows = ledger["requests"]
    require(
        len(rows) == len({row["id"] for row in rows}) == 10
        and reserved <= {row["id"] for row in rows},
        "ten-row prior/new ledger identity mismatch",
    )
    require(
        sum(row["spent"] for row in rows if row["spent"] is not None) == 863500
        and sum(row["reserved"] for row in rows if row["spent"] is None) == 4299300,
        "cumulative known/unknown rows do not reconcile",
    )
    finance = load(root / "finance-1821/r2-postclosure-financial.public.json")
    require(
        finance["financial_final"] is False
        and finance["new_gemini_attempts_recorded"]
        == finance["scored_game_requests"]
        == 0,
        "financial scope forged",
    )
    require(
        finance["new_known_spent_nanousd"] == 285800
        and finance["new_unknown_reserved_nanousd"] == 942250
        and finance["new_complete_liability_nanousd"] == 1228050,
        "new liability changed",
    )
    require(
        finance["cumulative_complete_liability_nanousd"]
        == report["cumulative_liability_nanousd"]
        == 5162800,
        "prior cost or unknown liability erased",
    )
    require(
        reserved == {item["request_id"] for item in finance["new_requests"]},
        "replay/Finance new request IDs differ",
    )
    claim = finance["recovery_claim"]
    require(
        claim["count"] == 1
        and claim["consumed"] is True
        and claim["data_field_read"] is False
        and claim["not_a_billable_request"] is True
        and claim["changed_by_audit"] is False,
        "retained claim forged or counted as a request",
    )
    require(
        finance["all_reconciliation_checks_pass"] is True
        and finance["execution_retry_performed"] is False,
        "Finance reconciliation/retry changed",
    )
    nested = load(root / "finance-1821/checksums.json")
    require(
        all(
            sha(root / "finance-1821" / name) == expected
            for name, expected in nested.get("files", nested).items()
        ),
        "Finance public originals changed",
    )
    inputs = load(root / "input-and-source-provenance.json")
    go = load(root / "historical-root-GO-projection.json")
    require(
        inputs["captured_role_count"] == len(inputs["captured_sha256"]) == 7
        and inputs["approved_payload_count"]
        == len(inputs["approved_inputs_sha256"])
        == 6,
        "six-plus-one input contract changed",
    )
    require(
        inputs["captured_sha256"] == go["captured_input_sha256_at_GO"]
        and go["source_revision"] == report["source_revision"],
        "captured GO/source mismatch",
    )
    require(
        go["source_receipt_sha256"]
        == "944a94de02ca12cd6a3a99ced89e9d902d2bf2a033e071d518d61c648b3b1f9c",
        "historical GO identity changed",
    )
    diagnostic = load(root / "safe-event-projection.public.json")
    require(
        diagnostic["copy_database"] == "<PRIVATE_DIAGNOSTIC_COPY>"
        and diagnostic["no_status_or_raw_output_added_to_evidence"] is True,
        "private path or missing raw evidence fabricated",
    )
    preservation = load(root / "private-copy-preservation.json")
    require(
        preservation["all_19_copy_hashes_sizes_mtimes_modes_owners_unchanged"] is True
        and preservation["original_f6_f7_or_canonical_opened"] is False
        and preservation["claim_or_reservation_mutations"] == 0,
        "closed-copy collection exceeded scope",
    )
    return {
        "verified_files": len(index),
        "synthetic_probe_events": len(events),
        "new_reserved_attempts": 3,
        "accounting_rows": 10,
        "claim_count": 1,
        "gemini_R2_evaluated": False,
        "scored_games": 0,
        "qualification_accepted": False,
        "financial_final": False,
        "cumulative_liability_nanousd": 5162800,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        print("Evidence verification failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
