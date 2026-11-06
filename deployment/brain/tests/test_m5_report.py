"""Evidence review must reject short horizons and preserve financial liabilities."""

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from canary_brain.recording import Manifest, RecordingStore, ReplayReader
from canary_brain.replay import export_archive

_spec = importlib.util.spec_from_file_location(
    "m5_report", Path(__file__).resolve().parents[1] / "tools/m5_report.py"
)
assert _spec is not None and _spec.loader is not None
reporter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reporter)


def evidence():
    prices = {
        "version": "fixture",
        "input_nanousd": 1,
        "output_nanousd": 2,
        "cached_nanousd": 1,
        "cache_write_nanousd": 1,
    }
    gateway = {
        "provider": "openai",
        "prices": prices,
        "effective_model": "model-a",
        "deployment_id": "deployment-a",
    }
    plan = {
        "name": "qa",
        "seconds": 1800,
        "repetitions": 1,
        "participants": [
            {"name": "native", "kind": "native", "gateway": None},
            {"name": "model", "kind": "litellm", "gateway": gateway},
        ],
        "expected_initial_sha256": "a" * 64,
        "memory_mode": "frozen",
        "source_revision": "f" * 40,
        "game_image": "sha256:" + "c" * 64,
        "database_image": "mariadb@sha256:" + "d" * 64,
        "run_cap_nanousd": 1000,
        "campaign_cap_nanousd": 2000,
    }
    experiment = {
        "plan": plan,
        "configuration_sha256": "b" * 64,
        "preflight": {
            "character": {
                "id": 7,
                "level": 20,
                "experience": 100,
                "posx": 1,
                "posy": 2,
                "posz": 7,
            }
        },
    }
    recordings, trials = [], []
    for participant in plan["participants"]:
        identity = f"qa:{participant['name']}:0"
        bot = {
            "id": 7,
            "level": 20,
            "xp": 100,
            "position": [1, 2, 7],
            "health": 100,
            "name": "QA",
            "vocation": 4,
            "state": "HUNTING",
            "mana": 100,
            "potions": 40,
            "alive": True,
        }
        events = [
            {
                "kind": "sample",
                "t_ms": 0,
                "wall": 1.0,
                "segment": "one",
                "data": {"bot": bot, "world": "qa", "objective_generation": 1},
            },
            {
                "kind": "lifecycle",
                "t_ms": 0,
                "wall": 1.0,
                "segment": "one",
                "data": {
                    "world": "qa",
                    "phase": "alive",
                    "deaths": 0,
                    "model_owned": False,
                },
            },
            {
                "kind": "sample",
                "t_ms": 1800000,
                "wall": 1801.0,
                "segment": "one",
                "data": {
                    "bot": {**bot, "xp": 110},
                    "world": "qa",
                    "objective_generation": 1,
                },
            },
            {
                "kind": "lifecycle",
                "t_ms": 1800000,
                "wall": 1801.0,
                "segment": "one",
                "data": {"phase": "run_supervisor_stop", "reason": "completed"},
            },
        ]
        if participant["kind"] == "litellm":
            events[1:1] = [
                {
                    "kind": "decision",
                    "t_ms": 1,
                    "data": {
                        "decision_id": "choice",
                        "phase": "requested",
                        "observation": {
                            "actions": [{"action": "hunt", "ttl_ms": 5000}]
                        },
                    },
                },
                {
                    "kind": "request",
                    "t_ms": 2,
                    "data": {
                        "request_id": "paid",
                        "decision_id": "choice",
                        "phase": "reserved",
                        "reserved_nanousd": 1000,
                        "deadline_ms": 5000,
                        "pricing_version": "fixture",
                    },
                },
                {
                    "kind": "request",
                    "t_ms": 12,
                    "data": {
                        "request_id": "paid",
                        "decision_id": "choice",
                        "phase": "finished",
                        "reserved_nanousd": 0,
                        "spent_nanousd": 14,
                        "elapsed_ms": 10,
                        "usage": {"input_tokens": 10, "output_tokens": 2},
                        "gateway": {"deployment_id": "deployment-a"},
                        "effective_model": "model-a",
                    },
                },
            ]
        recordings.append(
            {
                "id": identity,
                "status": "completed",
                "incomplete": False,
                "manifest": {
                    "participant": participant["name"],
                    "initial_sha256": "a" * 64,
                    "configuration_sha256": "b" * 64,
                    "memory_mode": "frozen",
                    "source_revision": "f" * 40,
                    "provider": "native"
                    if participant["kind"] == "native"
                    else "openai",
                },
                "events": events,
            }
        )
        trials.append(
            {
                "run_id": identity,
                "reason": "completed",
                "elapsed_seconds": 1800,
                "observed_seconds": 1800,
                "initial_character": {
                    "id": 7,
                    "level": 20,
                    "experience": 100,
                    "posx": 1,
                    "posy": 2,
                    "posz": 7,
                },
                "saved_character": {"id": 7, "level": 20, "experience": 110},
                "game_image": plan["game_image"],
                "database_image": plan["database_image"],
                "images_verified": True,
                "resources_cleaned": True,
            }
        )
    ledger = {
        "authority": "canonical-test-export",
        "month": "2026-11",
        "snapshot_utc": "2026-11-06T12:00:00Z",
        "budget": {
            "cap": 50 * reporter.USD,
            "spent": 14,
            "reserved": 0,
            "available": 50 * reporter.USD - 14,
        },
        "requests": [
            {
                "id": "paid",
                "month": "2026-11",
                "run_id": "qa:model:0",
                "reserved": 1000,
                "spent": 14,
            }
        ],
    }
    return experiment, recordings, trials, ledger


def codes(result):
    return {f["code"] for f in result["findings"]}


def test_complete_consistent_evidence_passes_without_infinite_native_efficiency():
    result = reporter.review(*evidence(), require_completed=True)
    assert result["ready_for_review"]
    assert result["settled_nanousd"] == 14
    assert result["unknown_nanousd"] == 0
    assert result["financial_totals_complete"]
    assert result["financial_final"]
    assert result["runs"][0]["xp_per_settled_dollar"] is None
    group = result["runs"][1]["latency"]["by_deadline_ms"]["5000"]
    assert group["completed_p95_ms"] == 10
    assert group["offered_ttl_ms"] == [5000]


def test_legacy_tolerance_does_not_accept_a_37ms_short_completed_run():
    args = evidence()
    args[1][0]["events"][-2]["t_ms"] = 1799963
    args[2][0]["observed_seconds"] = 1799.963
    result = reporter.review(*args, require_completed=True)
    assert "horizon_short" in codes(result)
    assert not result["ready_for_review"]


@pytest.mark.parametrize("require_completed", [False, True])
@pytest.mark.parametrize(
    "seconds,span,accepted",
    [
        (1800, 1800, True),
        (1800, 1805, True),
        (1800, 1805.001, False),
        (1800, 3600, False),
        (10, 15, True),
        (10, 15.001, False),
    ],
)
def test_completed_horizon_has_a_five_second_upper_bound(
    seconds, span, accepted, require_completed
):
    args = evidence()
    args[0]["plan"]["seconds"] = seconds
    for index in range(2):
        args[1][index]["events"][-2]["t_ms"] = round(span * 1000)
        args[2][index].update(elapsed_seconds=span, observed_seconds=span)
    result = reporter.review(*args, require_completed=require_completed)
    assert result["ready_for_review"] is accepted
    assert ("horizon_exceeded" in codes(result)) is not accepted
    assert result["maximum_completed_seconds"] == seconds + 5


@pytest.mark.parametrize("field", ["elapsed_seconds", "observed_seconds"])
def test_worker_clock_overrun_alone_blocks_completed_acceptance(field):
    args = evidence()
    args[2][0][field] = 3600
    assert "horizon_exceeded" in codes(reporter.review(*args))


def test_sample_span_overrun_alone_blocks_completed_acceptance():
    args = evidence()
    args[1][0]["events"][-2]["t_ms"] = 3600000
    assert "horizon_exceeded" in codes(reporter.review(*args))


@pytest.mark.parametrize(
    "reason,status", [("stalled", "failed"), ("budget_stop", "budget_stop")]
)
def test_upper_horizon_gate_does_not_relabel_failed_or_budget_outcomes(reason, status):
    args = evidence()
    args[1][0].update(status=status)
    args[1][0]["events"][-1]["data"]["reason"] = reason
    args[1][0]["events"][-2]["t_ms"] = 3600000
    args[2][0].update(reason=reason, elapsed_seconds=3600, observed_seconds=3600)
    result = reporter.review(*args)
    assert result["ready_for_review"]
    assert result["runs"][0]["status"] == status
    assert "horizon_exceeded" not in codes(result)


def test_tolerance_cannot_be_enlarged_to_conceal_a_double_length_run():
    args = evidence()
    args[0]["horizon_tolerance_seconds"] = 1800
    with pytest.raises(ValueError, match="zero to five seconds"):
        reporter.review(*args)


def test_unknown_timeout_remains_a_liability_and_is_not_success_latency():
    args = evidence()
    failed = next(
        e
        for e in args[1][1]["events"]
        if e["kind"] == "request" and e["data"]["phase"] == "finished"
    )
    failed["data"] = {
        "request_id": "paid",
        "phase": "failed",
        "error": "TimeoutError",
        "reserved_nanousd": 1000,
        "elapsed_ms": 5001,
    }
    args[3]["requests"][0]["spent"] = None
    args[3]["budget"].update(spent=0, reserved=1000, available=50 * reporter.USD - 1000)
    result = reporter.review(*args)
    assert result["ready_for_review"]
    assert result["unknown_nanousd"] == 1000
    assert result["settled_nanousd"] == 0
    assert result["financial_totals_complete"]
    assert not result["financial_final"]
    text = reporter.markdown(result)
    assert "Financial final: False" in text
    assert "Confirmed usage-priced spend: USD 0.000000000" in text
    assert "unknown liability retained: USD 0.000001000" in text
    run = result["runs"][1]
    assert run["xp_per_settled_dollar"] is None
    group = run["latency"]["by_deadline_ms"]["5000"]
    assert group["timeouts"] == 1
    assert group["completed_p95_ms"] is None


def test_incomplete_financial_coverage_is_not_final_even_when_unknown_total_is_zero():
    args = evidence()
    args[3]["requests"] = []
    result = reporter.review(*args)
    assert "request_ledger_set_mismatch" in codes(result)
    assert result["unknown_nanousd"] == 0
    assert not result["financial_totals_complete"]
    assert not result["financial_final"]
    assert not result["ready_for_review"]


def test_explicit_zero_settlement_is_final_with_complete_financial_coverage():
    args = evidence()
    prices = args[0]["plan"]["participants"][1]["gateway"]["prices"]
    for key in (
        "input_nanousd",
        "output_nanousd",
        "cached_nanousd",
        "cache_write_nanousd",
    ):
        prices[key] = 0
    terminal = next(
        event["data"]
        for event in args[1][1]["events"]
        if event["kind"] == "request" and event["data"]["phase"] == "finished"
    )
    terminal["spent_nanousd"] = 0
    args[3]["requests"][0]["spent"] = 0
    args[3]["budget"].update(spent=0, available=50 * reporter.USD)
    result = reporter.review(*args)
    assert result["ready_for_review"]
    assert result["settled_nanousd"] == result["unknown_nanousd"] == 0
    assert result["financial_totals_complete"]
    assert result["financial_final"]


@pytest.mark.parametrize("additional", [False, True])
def test_unknown_additional_or_unexpected_attempt_prevents_financial_final(additional):
    args = evidence()
    identity = "prior-probe" if additional else "qa:unexpected:0"
    if additional:
        args[0].update(additional_cost_run_ids=[identity], total_cap_nanousd=2000)
    args[3]["requests"].append(
        {
            "id": "unknown-extra",
            "month": "2026-10",
            "run_id": identity,
            "reserved": 400,
            "spent": None,
        }
    )
    args[3]["budget"].update(reserved=400, available=50 * reporter.USD - 414)
    result = reporter.review(*args)
    assert result["financial_totals_complete"]
    assert result["unknown_nanousd"] == 400
    assert not result["financial_final"]
    assert result["ready_for_review"] is additional
    assert ("unexpected_ledger_run" in codes(result)) is not additional


def test_budget_header_cannot_omit_unknown_liability_even_from_previous_month():
    args = evidence()
    failed = next(
        e
        for e in args[1][1]["events"]
        if e["kind"] == "request" and e["data"]["phase"] == "finished"
    )
    failed["data"] = {
        "request_id": "paid",
        "phase": "failed",
        "error": "TimeoutError",
        "reserved_nanousd": 1000,
        "elapsed_ms": 5001,
    }
    args[3]["requests"][0].update(spent=None, month="2026-10")
    result = reporter.review(*args)
    assert "monthly_reserved_understates_rows" in codes(result)
    assert result["unknown_nanousd"] == 1000
    assert not result["ready_for_review"] and not result["financial_totals_complete"]


def test_budget_header_cannot_omit_current_month_settled_charges():
    args = evidence()
    args[3]["budget"].update(spent=0, available=50 * reporter.USD)
    result = reporter.review(*args)
    assert "monthly_spent_understates_rows" in codes(result)
    assert result["settled_nanousd"] == 14


def test_prior_month_settled_charges_do_not_have_to_appear_in_current_month_spend():
    args = evidence()
    args[3]["requests"][0]["month"] = "2026-10"
    args[3]["budget"].update(spent=0, available=50 * reporter.USD)
    assert reporter.review(*args)["ready_for_review"]


@pytest.mark.parametrize(
    "snapshot,month",
    [
        (None, "2026-11"),
        ("2026-11-06T12:00:00", "2026-11"),
        ("2026-11-06T09:00:00-03:00", "2026-11"),
        ("2026-11-01T01:00:00Z", "2026-11"),
    ],
)
def test_ledger_snapshot_requires_utc_and_the_corresponding_sao_paulo_month(
    snapshot, month
):
    args = evidence()
    args[3].update(snapshot_utc=snapshot, month=month)
    assert "monthly_snapshot_time_invalid" in codes(reporter.review(*args))


def test_unplanned_trial_and_charge_are_retained_and_block_acceptance():
    args = evidence()
    args[2].append({**args[2][1], "run_id": "qa:model:replacement"})
    args[3]["requests"].append(
        {
            "id": "replacement",
            "month": "2026-11",
            "run_id": "qa:model:replacement",
            "reserved": 2000,
            "spent": 1000,
        }
    )
    args[3]["budget"].update(spent=1014, available=50 * reporter.USD - 1014)
    result = reporter.review(*args)
    assert {"unexpected_trial", "unexpected_ledger_run"} <= codes(result)
    assert result["settled_nanousd"] == 1014
    assert result["unplanned_spent_nanousd"] == 1000
    assert result["unplanned_cost_run_ids"] == ["qa:model:replacement"]
    assert not result["ready_for_review"]


def test_namespace_only_charge_is_not_hidden_when_trial_artifacts_are_missing():
    args = evidence()
    args[3]["requests"].append(
        {
            "id": "replacement",
            "month": "2026-11",
            "run_id": "qa:other:0",
            "reserved": 1000,
            "spent": None,
        }
    )
    args[3]["budget"].update(reserved=1000, available=50 * reporter.USD - 1014)
    result = reporter.review(*args)
    assert "unexpected_ledger_run" in codes(result)
    assert result["unknown_nanousd"] == 1000
    assert result["unplanned_unknown_nanousd"] == 1000


def test_request_created_after_export_snapshot_is_rejected_when_timestamp_present():
    args = evidence()
    args[3]["requests"][0]["created"] = 2_000_000_000
    result = reporter.review(*args)
    assert "ledger_row_after_snapshot" in codes(result)
    assert not result["ready_for_review"]


def test_monthly_cap_excess_is_reported_even_when_ledger_arithmetic_is_consistent():
    args = evidence()
    args[3]["budget"].update(spent=51 * reporter.USD, available=0)
    assert "monthly_cap_exceeded" in codes(reporter.review(*args))


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (lambda a: a[1].append(copy.deepcopy(a[1][0])), "duplicate_recording"),
        (
            lambda a: a[2][0].update(
                saved_character={"id": 7, "experience": 999, "level": 20}
            ),
            "saved_progress_mismatch",
        ),
        (
            lambda a: a[2][0].update(database_image="mariadb:11.4"),
            "image_identity_mismatch",
        ),
        (lambda a: a[2][0].update(resources_cleaned=False), "cleanup_unverified"),
        (lambda a: a[3]["requests"][0].update(spent=15), "settlement_mismatch"),
    ],
)
def test_inconsistent_evidence_fails_review(mutation, expected):
    args = evidence()
    mutation(args)
    result = reporter.review(*args)
    assert expected in codes(result)
    assert not result["ready_for_review"]


def test_missing_replay_does_not_hide_a_settled_canonical_charge():
    args = evidence()
    args[1].pop()
    result = reporter.review(*args)
    assert "missing_attempt_evidence" in codes(result)
    assert result["settled_nanousd"] == 14


def test_runtimeerror_is_not_fabricated_into_exact_backoff_or_ttl_counts():
    args = evidence()
    args[1][1]["events"].append(
        {
            "kind": "lifecycle",
            "t_ms": 100,
            "data": {"phase": "native_fallback", "reason": "RuntimeError"},
        }
    )
    result = reporter.review(*args)
    latency = result["runs"][1]["latency"]
    assert latency["exact_backoff_skips"] is None
    assert latency["runtime_error_fallbacks_unclassified"] == 1


def test_instrumented_backoff_count_requires_declared_capability_even_for_zero():
    args = evidence()
    before = reporter.review(*args)["runs"][1]["latency"]
    assert before["exact_backoff_skips"] is None
    args[0]["instrumentation"] = {"provider_backoff_classification": "ProviderBackoff"}
    empty = reporter.review(*args)["runs"][1]["latency"]
    assert empty["exact_backoff_skips"] == 0
    args[1][1]["events"].append(
        {
            "kind": "lifecycle",
            "t_ms": 100,
            "data": {"phase": "native_fallback", "reason": "ProviderBackoff"},
        }
    )
    classified = reporter.review(*args)["runs"][1]["latency"]
    assert classified["exact_backoff_skips"] == 1
    assert classified["backoff_by_deadline_ms"] is None


def test_recorded_backoff_skip_is_not_a_billable_attempt_or_timeout_denominator():
    args = evidence()
    args[0]["instrumentation"] = {"request_backoff_events": True}
    args[1][1]["events"].extend(
        [
            {
                "kind": "request",
                "t_ms": 100,
                "data": {
                    "request_id": "not-transmitted",
                    "decision_id": "choice",
                    "phase": "skipped",
                    "reason": "backoff",
                    "deadline_ms": 5000,
                    "reserved_nanousd": 0,
                },
            },
            {
                "kind": "lifecycle",
                "t_ms": 100,
                "data": {"phase": "native_fallback", "reason": "ProviderBackoff"},
            },
        ]
    )
    result = reporter.review(*args)
    assert result["ready_for_review"]
    assert result["settled_nanousd"] == 14
    row = result["runs"][1]
    assert len(row["requests"]) == 1 and len(row["skipped_requests"]) == 1
    assert row["latency"]["exact_backoff_skips"] == 1
    assert row["latency"]["backoff_by_deadline_ms"] == {"5000": 1}
    assert row["latency"]["by_deadline_ms"]["5000"]["reserved_attempts"] == 1
    assert row["latency"]["by_deadline_ms"]["5000"]["timeout_rate"] == 0


def test_mutable_digest_lookalike_does_not_qualify_as_immutable_image():
    args = evidence()
    args[0]["plan"]["game_image"] = "sha256:not-a-real-digest"
    args[2][0]["game_image"] = args[0]["plan"]["game_image"]
    assert "image_identity_mismatch" in codes(reporter.review(*args))


def test_custom_run_id_map_cannot_omit_a_paid_participant_or_its_cost():
    args = evidence()
    args[0]["plan"]["expected_runs"] = [
        {"run_id": "qa:native:0", "participant": "native", "repetition": 0}
    ]
    args[1].pop()
    args[2].pop()
    with pytest.raises(ValueError, match="full participant/repetition grid"):
        reporter.review(*args)


def test_unpriced_cache_writes_allow_zero_but_never_settle_positive_writes():
    args = evidence()
    args[0]["plan"]["participants"][1]["gateway"]["prices"]["cache_write_nanousd"] = (
        None
    )
    assert reporter.review(*args)["ready_for_review"]
    finished = next(
        e
        for e in args[1][1]["events"]
        if e["kind"] == "request" and e["data"]["phase"] == "finished"
    )
    finished["data"]["usage"]["input_tokens_details"] = {"cache_write_tokens": 1}
    result = reporter.review(*args)
    assert "usage_price_mismatch" in codes(result)
    assert result["settled_nanousd"] == 14


@pytest.mark.parametrize(
    "bad_probe,expected",
    [
        (None, "additional_cost_missing"),
        (
            {"id": "bad", "run_id": "prior-probe", "reserved": 100, "spent": -1000},
            "invalid_ledger_amount",
        ),
        (
            {"id": "bad", "run_id": "prior-probe", "reserved": "1000", "spent": None},
            "invalid_ledger_amount",
        ),
    ],
)
def test_missing_or_invalid_probe_liability_cannot_be_hidden_as_zero(
    bad_probe, expected
):
    args = evidence()
    args[0].update(additional_cost_run_ids=["prior-probe"], total_cap_nanousd=2000)
    if bad_probe:
        args[3]["requests"].append(bad_probe)
    result = reporter.review(*args)
    assert expected in codes(result)
    assert not result["ready_for_review"]
    assert not result["financial_totals_complete"]


def test_internally_consistent_but_different_initial_character_is_rejected():
    args = evidence()
    args[2][0]["initial_character"]["experience"] = 200
    args[2][0]["saved_character"]["experience"] = 210
    args[1][0]["events"][0]["data"]["bot"]["xp"] = 200
    args[1][0]["events"][-2]["data"]["bot"]["xp"] = 210
    result = reporter.review(*args, require_completed=True)
    assert "initial_fixture_mismatch" in codes(result)
    assert not result["ready_for_review"]


def cli_inputs(tmp_path, monkeypatch, *, trials_root=False):
    experiment, recordings, trials, ledger = evidence()
    for name, value in (
        ("experiment.json", experiment),
        ("trials.json", {"trials": trials}),
        ("ledger.json", ledger),
    ):
        (tmp_path / name).write_text(json.dumps(value))
    recording = tmp_path / "recording.sqlite3"
    recording.write_bytes(b"read-only-fixture")
    option = (
        ["--trials-root", str(tmp_path)]
        if trials_root
        else ["--trials", str(tmp_path / "trials.json")]
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "m5_report.py",
            "--recording",
            str(recording),
            "--experiment",
            str(tmp_path / "experiment.json"),
            "--ledger",
            str(tmp_path / "ledger.json"),
            "--output",
            str(tmp_path / "result"),
            *option,
        ],
    )
    return experiment, recordings, trials


def test_plan_changed_between_first_hash_and_json_read_is_rejected(
    tmp_path, monkeypatch
):
    experiment, _, _ = cli_inputs(tmp_path, monkeypatch)
    original = reporter.input_hashes
    calls = 0

    def change_after_hash(paths):
        nonlocal calls
        snapshot = original(paths)
        calls += 1
        if calls == 1:
            experiment["plan"]["seconds"] = 9999
            (tmp_path / "experiment.json").write_text(json.dumps(experiment))
        return snapshot

    monkeypatch.setattr(reporter, "input_hashes", change_after_hash)
    with pytest.raises(ValueError, match="Inputs changed"):
        reporter.main()
    assert not (tmp_path / "result").exists()


def test_trial_file_appearing_after_initial_hash_is_rejected(tmp_path, monkeypatch):
    _, recordings, trials = cli_inputs(tmp_path, monkeypatch, trials_root=True)
    monkeypatch.setattr(reporter, "load_recordings", lambda paths: recordings)

    def create_trial_files(*args):
        folder = tmp_path / "native-0"
        folder.mkdir()
        (folder / "saved-character.json").write_text(
            json.dumps(trials[0]["saved_character"])
        )
        return trials

    monkeypatch.setattr(reporter, "trials_from_root", create_trial_files)
    with pytest.raises(ValueError, match="Inputs changed during review"):
        reporter.main()
    assert not (tmp_path / "result").exists()


def test_changed_fixture_fingerprint_and_missing_native_death_evidence_are_visible():
    args = evidence()
    args[1][0]["manifest"]["initial_sha256"] = "e" * 64
    args[1][0]["events"] = [
        e for e in args[1][0]["events"] if e["data"].get("phase") != "alive"
    ]
    result = reporter.review(*args)
    assert {"manifest_mismatch", "death_telemetry_missing"} <= codes(result)


def test_prior_probe_costs_remain_in_the_total_envelope():
    args = evidence()
    args[0].update(additional_cost_run_ids=["prior-probe"], total_cap_nanousd=2000)
    args[3]["requests"].append(
        {
            "id": "probe",
            "run_id": "prior-probe",
            "month": "2026-11",
            "reserved": 100,
            "spent": 20,
        }
    )
    args[3]["budget"].update(spent=34, available=50 * reporter.USD - 34)
    result = reporter.review(*args)
    assert result["settled_nanousd"] == 34
    assert result["ready_for_review"]
    args[0]["total_cap_nanousd"] = 30
    assert "campaign_cap_exceeded" in codes(reporter.review(*args))


def test_archive_import_and_cli_are_read_only_and_refuse_mixed_rerun_output(tmp_path):
    experiment, recordings, trials, ledger = evidence()
    database = tmp_path / "source.sqlite3"
    store = RecordingStore(database)
    archives = []
    for row in recordings:
        manifest = Manifest(run_id=row["id"], bot_id=7, lineage="qa", **row["manifest"])
        store.begin(manifest)
        for index, event in enumerate(row["events"]):
            store.append(
                {
                    "run": row["id"],
                    "key": str(index),
                    "segment": "one",
                    "wall": 1.0,
                    **event,
                }
            )
        store.finish(row["id"], row["status"])
        archive = tmp_path / (row["manifest"]["participant"] + ".replay.zip")
        export_archive(ReplayReader(database), row["id"], archive)
        archives.append(archive)
    for filename, value in (
        ("experiment.json", experiment),
        ("trials.json", {"trials": trials}),
        ("ledger.json", ledger),
    ):
        (tmp_path / filename).write_text(json.dumps(value))
    before = {p: p.read_bytes() for p in archives}
    sqlite_before = {p.name: p.read_bytes() for p in tmp_path.glob("source.sqlite3*")}
    assert len(reporter.load_recordings([database])) == 2
    assert sqlite_before == {
        p.name: p.read_bytes() for p in tmp_path.glob("source.sqlite3*")
    }
    loaded = reporter.load_recordings(archives)
    assert reporter.review(experiment, loaded, trials, ledger)["ready_for_review"]
    command = [
        sys.executable,
        str(Path(reporter.__file__)),
        "--experiment",
        str(tmp_path / "experiment.json"),
        "--trials",
        str(tmp_path / "trials.json"),
        "--ledger",
        str(tmp_path / "ledger.json"),
        "--output",
        str(tmp_path / "report"),
    ]
    for archive in archives:
        command.extend(["--recording", str(archive)])
    first = subprocess.run(command, capture_output=True, text=True, check=False)
    assert first.returncode == 0, first.stderr
    acceptance = json.loads((tmp_path / "report/acceptance.json").read_text())
    assert acceptance["financial_totals_complete"]
    assert acceptance["financial_final"]
    report = (tmp_path / "report/report.json").read_bytes()
    second = subprocess.run(command, capture_output=True, text=True, check=False)
    assert second.returncode != 0
    assert (tmp_path / "report/report.json").read_bytes() == report
    assert before == {p: p.read_bytes() for p in archives}
