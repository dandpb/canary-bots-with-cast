"""Prospective recovery must retain every prior financial liability."""

import json
import sqlite3
from contextlib import closing

import pytest
import test_m5_pilot as pilot_fixtures
from test_m5_pilot import (
    admit_short_deadline_policy,
    approve_inputs,
    write,
)

from canary_brain.store import month_now
from tools import m5_pilot as pilot

admitted = pilot_fixtures.admitted

POLICY = "short_deadline_performance_recovery_v2"
OLD_NAMESPACE = "m5-og-20261106-dae4b84b"
OPENAI_RUN = "decisions:e9b235a5fcd24566b020fc332cd44e0d:65001"
GEMINI_RUN = "decisions:3f5394354a1a43ef8072c99256c4cbb3:65001"
HISTORICAL = [
    {
        "id": "8e32e915ca5e4407a3ec55ab501bd99a",
        "provider": "openai",
        "spent_nanousd": 52_800,
    },
    {
        "id": "57f0becd17ab47a2ad3638987ca2f6ef",
        "provider": "gemini",
        "spent_nanousd": 161_800,
    },
]


def change_json(plan, path, mutate):
    data = json.loads(path.read_text())
    mutate(data)
    write(path, data)
    approve_inputs(plan)


@pytest.fixture
def recovery(admitted):
    admit_short_deadline_policy(admitted)
    change_json(
        admitted,
        admitted.admission,
        lambda data: data.update(probe_outcome_policy=POLICY),
    )
    change_json(
        admitted,
        admitted.campaign,
        lambda data: data.update(name="qa-recovery"),
    )
    change_json(
        admitted,
        admitted.authorization,
        lambda data: data.update(
            max_total_nanousd=7_000_000_000,
            historical_requests=HISTORICAL,
            additional_cost_run_ids=[OPENAI_RUN, GEMINI_RUN],
        ),
    )
    # Only this temporary fixture is written; no canonical path is used.
    with closing(sqlite3.connect(admitted.canonical_ledger_file)) as db, db:
        for previous, historical in zip(
            ("old-openai", "old-gemini"), HISTORICAL, strict=True
        ):
            db.execute(
                "UPDATE requests SET id=? WHERE id=?", (historical["id"], previous)
            )
        db.executemany(
            "INSERT INTO requests(id,month,reserved,spent,endpoint,run_id) VALUES(?,?,?,?,?,?)",
            [
                (
                    "prior-openai-1",
                    month_now(),
                    825_375,
                    133_900,
                    "responses",
                    OPENAI_RUN,
                ),
                (
                    "prior-openai-2",
                    month_now(),
                    825_500,
                    53_400,
                    "responses",
                    OPENAI_RUN,
                ),
                (
                    "prior-openai-unknown",
                    month_now(),
                    942_250,
                    None,
                    "responses",
                    OPENAI_RUN,
                ),
                (
                    "prior-gemini-1",
                    month_now(),
                    2_414_500,
                    175_800,
                    "responses",
                    GEMINI_RUN,
                ),
                (
                    "prior-gemini-unknown",
                    month_now(),
                    2_414_800,
                    None,
                    "responses",
                    GEMINI_RUN,
                ),
            ],
        )
    return admitted


def test_recovery_counts_both_prior_runs_without_a_gemini_summary(recovery):
    result = pilot.preflight(recovery)
    assert result["accepted"] is True
    assert result["historical_nanousd"] == 3_934_750
    assert result["new_worst_case_nanousd"] == 6_980_000_000
    assert (
        result["historical_nanousd"] + result["new_worst_case_nanousd"] == 6_983_934_750
    )
    assert result["budget"]["spent"] == 577_700
    assert result["budget"]["reserved"] == 3_357_050
    with closing(sqlite3.connect(recovery.canonical_ledger_file)) as db:
        assert db.execute(
            "SELECT reserved,spent FROM requests WHERE id=?",
            ("prior-gemini-unknown",),
        ).fetchone() == (2_414_800, None)


def test_recovery_keeps_explicit_known_zero_distinct_from_unknown(recovery):
    with closing(sqlite3.connect(recovery.canonical_ledger_file)) as db, db:
        db.execute("UPDATE requests SET spent=0 WHERE id=?", ("prior-openai-1",))
    result = pilot.preflight(recovery)
    assert result["historical_nanousd"] == 3_800_850
    assert result["budget"]["reserved"] == 3_357_050


async def test_recovery_runs_each_new_fake_qualification_once_with_its_actual_policy(
    recovery, monkeypatch
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    calls = pilot_fixtures.fake_probe_sdk(monkeypatch)
    games = []

    async def fake_game(experiment):
        games.append(experiment)
        return {"offline": True}

    monkeypatch.setattr(pilot, "run_attested_campaign", fake_game)
    result = await pilot.execute(recovery)
    assert len(calls) == 6 and len(games) == 1
    for provider in ("openai", "gemini"):
        probe = result["probes"][provider]
        assert probe["qualification"]["policy"] == POLICY
        assert probe["qualification"]["accepted_for_game"] is True
        assert probe["qualification"]["unknown_requests"] == 1
        assert probe["qualification"]["financial_final"] is False
        assert not set(probe["runs"]) & {OPENAI_RUN, GEMINI_RUN}


@pytest.mark.parametrize(
    "extra_runs",
    [
        None,
        [],
        [OPENAI_RUN],
        [GEMINI_RUN],
        [OPENAI_RUN, OPENAI_RUN],
        [OPENAI_RUN, GEMINI_RUN, "undeclared-extra"],
        [OPENAI_RUN, "credential-smoke-out-openai"],
        [OPENAI_RUN, True],
        OPENAI_RUN,
    ],
)
def test_recovery_cannot_omit_duplicate_or_silently_ignore_prior_runs(
    recovery, extra_runs
):
    change_json(
        recovery,
        recovery.authorization,
        lambda data: data.update(additional_cost_run_ids=extra_runs),
    )
    with pytest.raises(ValueError, match="recovery"):
        pilot.preflight(recovery)


def test_recovery_requires_the_canonical_gemini_run_even_without_a_summary(recovery):
    with closing(sqlite3.connect(recovery.canonical_ledger_file)) as db, db:
        db.execute("DELETE FROM requests WHERE run_id=?", (GEMINI_RUN,))
    with pytest.raises(ValueError, match="prior.*run|run.*missing"):
        pilot.preflight(recovery)


@pytest.mark.parametrize("spent", [None, True, 52_800.0, "52800", -1])
def test_recovery_requires_exact_integer_historical_amounts(recovery, spent):
    def changed(data):
        data["historical_requests"][0]["spent_nanousd"] = spent

    change_json(recovery, recovery.authorization, changed)
    with pytest.raises(ValueError, match="recovery"):
        pilot.preflight(recovery)


def test_recovery_cannot_duplicate_a_historical_request(recovery):
    change_json(
        recovery,
        recovery.authorization,
        lambda data: data.update(historical_requests=[HISTORICAL[0], HISTORICAL[0]]),
    )
    with pytest.raises(ValueError, match="recovery"):
        pilot.preflight(recovery)


@pytest.mark.parametrize(
    ("field", "amount"),
    [
        ("max_total_nanousd", 7_000_000_000.0),
        ("max_total_nanousd", True),
        ("max_total_nanousd", 6_980_214_600),
        ("canonical_monthly_cap_nanousd", 50_000_000_000.0),
    ],
)
def test_recovery_envelope_keeps_strict_integer_caps(recovery, field, amount):
    change_json(
        recovery,
        recovery.authorization,
        lambda data: data.update({field: amount}),
    )
    with pytest.raises(ValueError, match="recovery"):
        pilot.preflight(recovery)


@pytest.mark.parametrize("one_over", [False, True])
def test_recovery_uses_the_complete_usd7_boundary(recovery, one_over):
    with closing(sqlite3.connect(recovery.canonical_ledger_file)) as db, db:
        db.execute(
            "UPDATE requests SET reserved=? WHERE id=?",
            (17_007_500 + int(one_over), "prior-openai-unknown"),
        )
    if one_over:
        with pytest.raises(ValueError, match="USD7"):
            pilot.preflight(recovery)
    else:
        result = pilot.preflight(recovery)
        assert result["historical_nanousd"] == 20_000_000
        assert (
            result["historical_nanousd"] + result["new_worst_case_nanousd"]
            == 7_000_000_000
        )


@pytest.mark.parametrize(
    ("column", "amount"),
    [
        ("reserved", 0),
        ("reserved", -1),
        ("reserved", 1.5),
        ("spent", -1),
        ("spent", "invalid"),
    ],
)
def test_recovery_does_not_let_sql_sum_coerce_invalid_prior_money(
    recovery, column, amount
):
    assert column in {"reserved", "spent"}
    with closing(sqlite3.connect(recovery.canonical_ledger_file)) as db, db:
        db.execute(
            f"UPDATE requests SET {column}=? WHERE id=?",
            (amount, "prior-openai-unknown"),
        )
    with pytest.raises(
        ValueError, match="prior.*amount|prior.*money|invalid.*liability"
    ):
        pilot.preflight(recovery)


def test_recovery_cannot_reuse_the_failed_campaign_namespace(recovery):
    change_json(
        recovery,
        recovery.campaign,
        lambda data: data.update(name=OLD_NAMESPACE),
    )
    with pytest.raises(ValueError, match="recovery|namespace"):
        pilot.preflight(recovery)


def test_v1_still_cannot_take_the_recovery_envelope(admitted):
    admit_short_deadline_policy(admitted)
    change_json(
        admitted,
        admitted.authorization,
        lambda data: data.update(max_total_nanousd=7_000_000_000),
    )
    with pytest.raises(ValueError, match="envelope"):
        pilot.preflight(admitted)


def test_original_strict_preflight_still_accepts_its_usd7_envelope(admitted):
    assert pilot.preflight(admitted)["accepted"] is True


def claim_offline(recovery):
    captured = pilot.capture_inputs(recovery)
    admitted = {"input_sha256": pilot.input_hashes(captured)}
    return pilot.claim_recovery(recovery, captured, admitted)


def test_recovery_claim_persists_and_blocks_a_second_namespace(recovery):
    first = pilot.preflight(recovery)
    assert first["historical_nanousd"] == 3_934_750
    claimed = claim_offline(recovery)
    assert claimed["historical_nanousd"] == first["historical_nanousd"]
    with closing(sqlite3.connect(recovery.canonical_ledger_file)) as db:
        row = db.execute(
            "SELECT data FROM records WHERE kind=? AND key=?",
            (pilot.RECOVERY_CLAIM_KIND, pilot.RECOVERY_CLAIM_KEY),
        ).fetchone()
    assert row is not None
    marker = json.loads(row[0])
    assert marker["namespace"] == "qa-recovery"
    assert marker["input_sha256"] == pilot.input_hashes(pilot.capture_inputs(recovery))

    change_json(
        recovery,
        recovery.campaign,
        lambda data: data.update(name="qa-recovery-again"),
    )
    with pytest.raises(ValueError, match="already been claimed"):
        pilot.preflight(recovery)
    with pytest.raises(ValueError, match="already been claimed"):
        claim_offline(recovery)


@pytest.mark.parametrize("drift", ["prior", "monthly", "missing_run", "history"])
def test_recovery_claim_revalidates_the_ledger_before_recording_use(recovery, drift):
    admitted = pilot.preflight(recovery)
    captured = pilot.capture_inputs(recovery)
    with closing(sqlite3.connect(recovery.canonical_ledger_file)) as db, db:
        if drift == "prior":
            db.execute(
                "UPDATE requests SET reserved=17007501 WHERE id='prior-openai-unknown'"
            )
        elif drift == "monthly":
            db.execute(
                "INSERT INTO requests(id,month,reserved,endpoint,run_id) "
                "VALUES(?,?,?,?,?)",
                ("other-monthly-charge", month_now(), 40_000_000_000, "", "other"),
            )
        elif drift == "missing_run":
            db.execute("DELETE FROM requests WHERE run_id=?", (GEMINI_RUN,))
        else:
            db.execute(
                "UPDATE requests SET spent=52801 WHERE id=?",
                (HISTORICAL[0]["id"],),
            )
    with pytest.raises(ValueError):
        pilot.claim_recovery(recovery, captured, admitted)
    with closing(sqlite3.connect(recovery.canonical_ledger_file)) as db:
        assert (
            db.execute(
                "SELECT 1 FROM records WHERE kind=? AND key=?",
                (pilot.RECOVERY_CLAIM_KIND, pilot.RECOVERY_CLAIM_KEY),
            ).fetchone()
            is None
        )


async def test_execute_claims_recovery_before_starting_any_probe(recovery, monkeypatch):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    monkeypatch.setattr(
        pilot,
        "preflight",
        lambda plan, captured: {"input_sha256": pilot.input_hashes(captured)},
    )

    async def before_probe(plan, admitted, captured):
        with closing(sqlite3.connect(plan.canonical_ledger_file)) as db:
            assert db.execute(
                "SELECT 1 FROM records WHERE kind=? AND key=?",
                (pilot.RECOVERY_CLAIM_KIND, pilot.RECOVERY_CLAIM_KEY),
            ).fetchone() == (1,)
        assert admitted["historical_nanousd"] == 3_934_750
        return {"offline": True}

    monkeypatch.setattr(pilot, "execute_admitted", before_probe)
    assert await pilot.execute(recovery) == {"offline": True}
    with pytest.raises(ValueError, match="already been claimed"):
        await pilot.execute(recovery)


async def test_failed_recovery_keeps_its_claim(recovery, monkeypatch):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    monkeypatch.setattr(
        pilot,
        "preflight",
        lambda plan, captured: {"input_sha256": pilot.input_hashes(captured)},
    )

    async def fail_after_claim(plan, admitted, captured):
        raise RuntimeError("offline probe failure")

    monkeypatch.setattr(pilot, "execute_admitted", fail_after_claim)
    with pytest.raises(RuntimeError, match="offline probe failure"):
        await pilot.execute(recovery)
    with pytest.raises(ValueError, match="already been claimed"):
        claim_offline(recovery)
