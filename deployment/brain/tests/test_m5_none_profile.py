"""One new explicit-none profile retains every prior attempt and consumed grant."""

import asyncio
import copy
import json
import multiprocessing
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

import pytest
import test_m5_pilot as fixtures
import test_m5_recovery_budget as recovery_fixtures

from canary_brain.store import month_now
from tools import m5_pilot as pilot

admitted = fixtures.admitted
recovery = recovery_fixtures.recovery
POLICY = "openai_none_performance_v3"
PROFILE = "openai_none_gemini_default_v1"
REFERENCE = Path(__file__).parents[1] / "tools/m5_openai_none_reference.v2.json"
REFERENCE_PATH = "deployment/brain/tools/m5_openai_none_reference.v2.json"


def change(plan, path, update):
    data = json.loads(path.read_text())
    update(data)
    fixtures.write(path, data)
    fixtures.approve_inputs(plan)


@pytest.fixture
def none_plan(admitted, monkeypatch):
    reference = json.loads(REFERENCE.read_text())
    campaign = copy.deepcopy(reference["functional_campaign"])
    original = json.loads(admitted.campaign.read_text())
    campaign.update(
        {
            key: original[key]
            for key in (
                "output",
                "fixture",
                "world_map",
                "budget_file",
                "gateway_credential",
                "source_revision",
            )
        }
    )
    campaign["name"] = "qa-none-profile"
    campaign["participants"][1]["gateway"]["decision_reasoning_effort"] = "none"
    fixtures.write(admitted.campaign, campaign)
    admitted.decision_fixtures.write_bytes(
        (Path(__file__).parent / "fixtures/m5-none-v3-decisions.json").read_bytes()
    )
    for name, path in admitted.probe_workers.items():
        previous = json.loads(path.read_text())
        config = copy.deepcopy(reference["functional_probe_controls"])
        config.update(
            {
                key: previous[key]
                for key in (
                    "socket_directory",
                    "state_file",
                    "budget_file",
                    "credential_file",
                )
            }
        )
        config["recording"].update(previous["recording"])
        config["gateway"] = copy.deepcopy(reference["gateway_profiles"][name])
        if name == "openai":
            config["gateway"]["decision_reasoning_effort"] = "none"
        fixtures.write(path, config)
    source = json.loads(admitted.source_manifest.read_text())
    asset = Path(source["source_path"]) / REFERENCE_PATH
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_bytes(REFERENCE.read_bytes())
    source["files"][REFERENCE_PATH] = pilot.file_hash(asset)
    fixtures.write(admitted.source_manifest, source)
    historical = [
        {"id": row["id"], "spent_nanousd": row["spent"]}
        for row in reference["prior_requests_as_observed"]
        if row["run_id"].startswith("credential-smoke-")
    ]
    runs = sorted(
        {
            row["run_id"]
            for row in reference["prior_requests_as_observed"]
            if row["run_id"].startswith("decisions:")
        }
    )
    change(
        admitted,
        admitted.authorization,
        lambda j: j.update(
            historical_requests=historical, additional_cost_run_ids=runs
        ),
    )
    change(
        admitted,
        admitted.admission,
        lambda j: j.update(
            probe_outcome_policy=POLICY,
            controller_profile=PROFILE,
            common_worker_image=reference["images"]["worker"],
            gateway_image=reference["images"]["gateway"],
            gateway_route_projection_sha256=reference[
                "gateway_route_projection_sha256"
            ],
            **reference["worker_dependency_versions"],
        ),
    )
    with closing(sqlite3.connect(admitted.canonical_ledger_file)) as db, db:
        db.execute("DELETE FROM requests")
        db.executemany(
            "INSERT INTO requests(id,month,reserved,spent,endpoint,run_id) VALUES(?,?,?,?,?,?)",
            [
                (
                    row["id"],
                    month_now(),
                    row["reserved"],
                    row["spent"],
                    "responses",
                    row["run_id"],
                )
                for row in reference["prior_requests_as_observed"]
            ],
        )
        db.execute(
            "INSERT INTO records(kind,key,data) VALUES(?,?,?)",
            ("m5_recovery_v2", "single_use", "malformed-but-consumed"),
        )
    # Keep infrastructure boundaries synthetic: no real map, credential or container.
    monkeypatch.setattr(
        pilot.benchmark, "fixture_hash", lambda *_: reference["fixture_sha256"]
    )
    monkeypatch.setattr(
        pilot,
        "NONE_GATEWAY_CREDENTIAL_FILE",
        Path(campaign["gateway_credential"]),
        raising=False,
    )
    original_hash = pilot.file_hash
    world = Path(campaign["world_map"])
    monkeypatch.setattr(
        pilot,
        "file_hash",
        lambda path: (
            reference["world_sha256"] if path == world else original_hash(path)
        ),
    )
    monkeypatch.setattr(
        pilot.platform,
        "python_version",
        lambda: reference["worker_dependency_versions"]["common_worker_python"],
    )
    versions = reference["worker_dependency_versions"]
    monkeypatch.setattr(
        pilot.importlib.metadata,
        "version",
        lambda name: versions[{"openai": "openai_sdk", "pydantic": "pydantic"}[name]],
    )
    monkeypatch.setattr(
        pilot,
        "container_identity",
        lambda: (
            reference["images"]["worker"],
            [
                {
                    "Type": "volume",
                    "Name": pilot.CANONICAL_VOLUME,
                    "Destination": str(admitted.canonical_ledger_file.parent),
                    "RW": True,
                }
            ],
        ),
    )
    plan = admitted.model_copy(update={"worker_image": reference["images"]["worker"]})
    fixtures.approve_inputs(plan)
    return plan


def test_explicit_none_preflight_counts_all_ten_without_consuming_the_new_grant(
    none_plan,
):
    result = pilot.preflight(none_plan)
    assert result["accepted"] is True
    assert result["historical_nanousd"] == 5_162_800
    assert (
        result["historical_nanousd"] + result["new_worst_case_nanousd"] == 6_985_162_800
    )
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db:
        assert db.execute(
            "SELECT COUNT(*) FROM records WHERE kind=? AND key=?",
            ("m5_openai_none_v3", "single_use"),
        ).fetchone() == (0,)
        assert db.execute("SELECT COUNT(*) FROM requests").fetchone() == (10,)


def test_default_reasoning_cannot_use_the_new_none_profile_grant(none_plan):
    change(
        none_plan,
        none_plan.campaign,
        lambda j: j["participants"][1]["gateway"].pop("decision_reasoning_effort"),
    )
    change(
        none_plan,
        none_plan.probe_workers["openai"],
        lambda j: j["gateway"].pop("decision_reasoning_effort"),
    )
    with pytest.raises(ValueError, match="explicit-none|profile"):
        pilot.preflight(none_plan)


async def test_none_grant_is_committed_before_the_first_probe_boundary(
    none_plan, monkeypatch
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    calls = []

    async def observe_before_probe(plan, admitted, captured):
        with closing(sqlite3.connect(plan.canonical_ledger_file)) as db:
            marker = db.execute(
                "SELECT data FROM records WHERE kind=? AND key=?",
                ("m5_openai_none_v3", "single_use"),
            ).fetchone()
        assert marker is not None
        marker = json.loads(marker[0])
        assert marker["policy"] == POLICY and marker["controller_profile"] == PROFILE
        assert marker["input_sha256"] == pilot.input_hashes(captured)
        assert marker["historical_nanousd"] == 5_162_800
        calls.append(marker["namespace"])
        return {"offline": True}

    monkeypatch.setattr(pilot, "execute_admitted", observe_before_probe)
    assert await pilot.execute(none_plan) == {"offline": True}
    change(
        none_plan,
        none_plan.campaign,
        lambda j: j.update(name="qa-none-another-namespace"),
    )
    with pytest.raises(ValueError, match="already been claimed"):
        await pilot.execute(none_plan)
    assert calls == ["qa-none-profile"]


@pytest.mark.parametrize(
    "request_id",
    [
        "8e32e915ca5e4407a3ec55ab501bd99a",
        "57f0becd17ab47a2ad3638987ca2f6ef",
        "0127734202e044e9aa93cc3261a82647",
        "742774dec9f94c4eb5c903b69bffe0aa",
        "c8f2779f524c49be9da807f71eeffd58",
        "b91f101ecf4a4d7ea2315922365e4193",
        "952c7a462a36461485d7fe37f3ee8444",
        "2ad399344ae54433b080c600156eefd6",
        "81c26627802f4161a43d40a0d0b1f26f",
        "847b421069fc4e19aeab9a1a3385c8d8",
    ],
)
@pytest.mark.parametrize("mutation", ["missing", "wrong_run"])
def test_none_requires_every_prior_identity_and_its_actual_run(
    none_plan, request_id, mutation
):
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db, db:
        if mutation == "missing":
            db.execute("DELETE FROM requests WHERE id=?", (request_id,))
        else:
            db.execute(
                "UPDATE requests SET run_id='unrelated' WHERE id=?", (request_id,)
            )
    with pytest.raises(ValueError, match="ten exact prior"):
        pilot.preflight(none_plan)


def test_none_rejects_an_unexpected_request_in_a_closed_prior_run(none_plan):
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db, db:
        db.execute(
            "INSERT INTO requests(id,month,reserved,spent,run_id) VALUES(?,?,?,?,?)",
            (
                "undeclared-closed-attempt",
                month_now(),
                1,
                0,
                "decisions:3f5394354a1a43ef8072c99256c4cbb3:65001",
            ),
        )
    with pytest.raises(ValueError, match="ten exact prior"):
        pilot.preflight(none_plan)


@pytest.mark.parametrize(
    ("column", "amount"),
    [
        ("reserved", 0),
        ("reserved", -1),
        ("reserved", 1.5),
        ("reserved", b"942250"),
        ("spent", -1),
        ("spent", "not-money"),
    ],
)
def test_none_rejects_prior_money_before_sql_sum_can_coerce_it(
    none_plan, column, amount
):
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db, db:
        db.execute(
            f"UPDATE requests SET {column}=? WHERE id=?",
            (amount, "847b421069fc4e19aeab9a1a3385c8d8"),
        )
    with pytest.raises(ValueError, match="prior money"):
        pilot.preflight(none_plan)


@pytest.mark.parametrize("one_over", [False, True])
def test_none_complete_liability_uses_the_exact_usd7_boundary(none_plan, one_over):
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db, db:
        db.execute(
            "UPDATE requests SET reserved=? WHERE id=?",
            (15_779_450 + int(one_over), "847b421069fc4e19aeab9a1a3385c8d8"),
        )
    if one_over:
        with pytest.raises(ValueError, match="USD7"):
            pilot.preflight(none_plan)
    else:
        assert pilot.preflight(none_plan)["historical_nanousd"] == 20_000_000


def test_none_known_zero_is_not_the_original_reserved_unknown(none_plan):
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db, db:
        db.execute(
            "UPDATE requests SET spent=0 WHERE id=?",
            ("2ad399344ae54433b080c600156eefd6",),
        )
    result = pilot.preflight(none_plan)
    assert result["historical_nanousd"] == 4_991_900
    assert result["budget"]["reserved"] == 4_299_300


@pytest.mark.parametrize(
    "namespace", ["M5-OG-20261106-DAE4B84B", "M5-OG-R2-20261106-27120D96"]
)
def test_none_cannot_relabel_either_closed_namespace(none_plan, namespace):
    change(none_plan, none_plan.campaign, lambda j: j.update(name=namespace.lower()))
    # The envelope validator is also used immediately before the claim.
    with pytest.raises(ValueError, match="fresh campaign namespace"):
        pilot.validate_none_envelope(
            json.loads(none_plan.authorization.read_text()), namespace
        )
    with pytest.raises(ValueError, match="fresh campaign namespace"):
        pilot.preflight(none_plan)


@pytest.mark.parametrize(
    "prior_runs",
    [
        None,
        [],
        ["wrong"],
        [True],
        [
            "decisions:e9b235a5fcd24566b020fc332cd44e0d:65001",
            "decisions:3f5394354a1a43ef8072c99256c4cbb3:65001",
        ],
    ],
)
def test_none_cannot_omit_prior_runs_from_the_envelope(none_plan, prior_runs):
    change(
        none_plan,
        none_plan.authorization,
        lambda j: j.update(additional_cost_run_ids=prior_runs),
    )
    with pytest.raises(ValueError, match="three prior runs"):
        pilot.preflight(none_plan)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_total_nanousd", 7_000_000_000.0),
        ("max_total_nanousd", True),
        ("canonical_monthly_cap_nanousd", 50_000_000_000.0),
    ],
)
def test_none_caps_require_exact_integer_contracts(none_plan, field, value):
    change(none_plan, none_plan.authorization, lambda j: j.update({field: value}))
    with pytest.raises(ValueError, match="exact USD7/USD50"):
        pilot.preflight(none_plan)


@pytest.mark.parametrize(
    "field",
    [
        "seed",
        "decision_timeout",
        "seconds",
        "game_image",
        "database_image",
        "new_option",
    ],
)
def test_coherent_campaign_edits_cannot_replace_the_reviewed_reference(
    none_plan, field
):
    def mutate(j):
        j[field] = {
            "seed": 43,
            "decision_timeout": 9,
            "seconds": 1799,
            "game_image": "sha256:" + "a" * 64,
            "database_image": "sha256:" + "b" * 64,
            "new_option": False,
        }[field]

    change(none_plan, none_plan.campaign, mutate)
    with pytest.raises(ValueError, match="functional reference"):
        pilot.preflight(none_plan)


@pytest.mark.parametrize("name", ["openai", "gemini"])
@pytest.mark.parametrize("effort", [None, "low", "none", False])
def test_only_the_exact_none_openai_and_omitted_gemini_profile_is_admitted(
    none_plan, name, effort
):
    change(
        none_plan,
        none_plan.probe_workers[name],
        lambda j: j["gateway"].update(decision_reasoning_effort=effort),
    )
    change(
        none_plan,
        none_plan.campaign,
        lambda j: j["participants"][1 if name == "openai" else 2]["gateway"].update(
            decision_reasoning_effort=effort
        ),
    )
    allowed = (name == "openai" and effort == "none") or (
        name == "gemini" and effort is None
    )
    if allowed:
        assert pilot.preflight(none_plan)["accepted"] is True
    else:
        with pytest.raises(ValueError, match="functional reference"):
            pilot.preflight(none_plan)


@pytest.mark.parametrize(
    "field",
    [
        "mode",
        "decision_timeout",
        "learning",
        "credential_file",
        "socket_directory",
        "state_file",
    ],
)
def test_probe_controls_and_identity_exclusions_do_not_hide_functional_drift(
    none_plan, field
):
    values = {
        "mode": "active",
        "decision_timeout": 10.0,
        "learning": False,
        "credential_file": "/different/internal/env",
        "socket_directory": "/tmp/unowned",
        "state_file": "/tmp/unowned.sqlite3",
    }
    change(
        none_plan,
        none_plan.probe_workers["openai"],
        lambda j: j.update({field: values[field]}),
    )
    with pytest.raises(ValueError, match="explicit-none"):
        pilot.preflight(none_plan)


def test_coherently_changed_prices_do_not_pass_merely_by_matching_both_configs(
    none_plan,
):
    change(
        none_plan,
        none_plan.campaign,
        lambda j: j["participants"][1]["gateway"]["prices"].update(output_nanousd=499),
    )
    change(
        none_plan,
        none_plan.probe_workers["openai"],
        lambda j: j["gateway"]["prices"].update(output_nanousd=499),
    )
    with pytest.raises(ValueError, match="functional reference"):
        pilot.preflight(none_plan)


@pytest.mark.parametrize("mutation", ["omitted", "bytes_and_manifest"])
def test_functional_reference_is_required_with_its_reviewed_bytes(none_plan, mutation):
    source = json.loads(none_plan.source_manifest.read_text())
    if mutation == "omitted":
        del source["files"][REFERENCE_PATH]
    else:
        asset = Path(source["source_path"]) / REFERENCE_PATH
        asset.write_text("{}")
        source["files"][REFERENCE_PATH] = pilot.file_hash(asset)
    fixtures.write(none_plan.source_manifest, source)
    fixtures.approve_inputs(none_plan)
    with pytest.raises(ValueError, match="reference.*manifest"):
        pilot.preflight(none_plan)


def test_duplicate_json_keys_cannot_be_normalized_into_an_approved_profile(none_plan):
    original = none_plan.campaign.read_text()
    none_plan.campaign.write_text('{"seconds":1800,' + original[1:])
    fixtures.approve_inputs(none_plan)
    with pytest.raises(ValueError, match="duplicate JSON key"):
        pilot.preflight(none_plan)


def claim(plan):
    captured = pilot.capture_inputs(plan)
    return pilot.claim_none_profile(
        plan, captured, {"input_sha256": pilot.input_hashes(captured)}
    )


@pytest.mark.parametrize("data", ["{}", "null", "broken"])
def test_any_existing_none_grant_blocks_another_invocation(none_plan, data):
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db, db:
        db.execute(
            "INSERT INTO records(kind,key,data) VALUES(?,?,?)",
            ("m5_openai_none_v3", "single_use", data),
        )
    with pytest.raises(ValueError, match="already been claimed"):
        pilot.preflight(none_plan)
    with pytest.raises(ValueError, match="already been claimed"):
        claim(none_plan)


def test_missing_consumed_v2_is_not_a_fresh_none_permission(none_plan):
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db, db:
        db.execute(
            "DELETE FROM records WHERE kind=? AND key=?",
            ("m5_recovery_v2", "single_use"),
        )
    with pytest.raises(ValueError, match="consumed recovery"):
        pilot.preflight(none_plan)


def test_concurrent_claims_can_commit_only_one_global_none_grant(none_plan):
    def attempt(_):
        try:
            claim(none_plan)
            return "committed"
        except ValueError as error:
            assert "already been claimed" in str(error)
            return "denied"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(attempt, range(2)))
    assert sorted(outcomes) == ["committed", "denied"]
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db:
        assert db.execute(
            "SELECT COUNT(*) FROM records WHERE kind=? AND key=?",
            ("m5_openai_none_v3", "single_use"),
        ).fetchone() == (1,)


async def test_failure_after_commit_keeps_none_consumed_without_a_second_probe(
    none_plan, monkeypatch
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    calls = []

    async def fail(*_):
        calls.append("probe")
        raise RuntimeError("offline failure after commit")

    monkeypatch.setattr(pilot, "execute_admitted", fail)
    with pytest.raises(RuntimeError, match="offline failure"):
        await pilot.execute(none_plan)
    with pytest.raises(ValueError, match="already been claimed"):
        await pilot.execute(none_plan)
    assert calls == ["probe"]


def test_process_death_after_commit_does_not_return_the_none_grant(none_plan):
    def commit_then_die():
        claim(none_plan)
        os._exit(19)

    process = multiprocessing.get_context("fork").Process(target=commit_then_die)
    process.start()
    try:
        process.join(10)
        assert process.exitcode == 19
    finally:
        if process.is_alive():
            process.terminate()
            process.join(5)
    with pytest.raises(ValueError, match="already been claimed"):
        pilot.preflight(none_plan)


@pytest.mark.parametrize(
    "policy",
    [None, "short_deadline_performance_v1", "short_deadline_performance_recovery_v2"],
)
def test_consumed_none_grant_closes_older_policy_paths(recovery, policy):
    with closing(sqlite3.connect(recovery.canonical_ledger_file)) as db, db:
        db.execute(
            "INSERT INTO records(kind,key,data) VALUES(?,?,?)",
            ("m5_openai_none_v3", "single_use", "null"),
        )
    if policy != "short_deadline_performance_recovery_v2":
        recovery_fixtures.admit_other_policy(
            recovery, policy, "qa-after-none", recovery_fixtures.HISTORICAL
        )
    with pytest.raises(ValueError, match="explicit-none.*already been claimed"):
        pilot.preflight(recovery)


@pytest.mark.parametrize(
    "drift", ["prior", "monthly", "missing_id", "missing_v2", "concurrent_claim"]
)
async def test_none_execution_rechecks_current_finance_and_claims_under_the_lease(
    none_plan, monkeypatch, drift
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    original = pilot.preflight

    def preflight_then_change(plan, captured):
        result = original(plan, captured)
        with closing(sqlite3.connect(plan.canonical_ledger_file)) as db, db:
            if drift == "prior":
                db.execute(
                    "UPDATE requests SET reserved=15779451 WHERE id=?",
                    ("847b421069fc4e19aeab9a1a3385c8d8",),
                )
            elif drift == "monthly":
                db.execute(
                    "INSERT INTO requests(id,month,reserved,spent,run_id) VALUES(?,?,?,?,?)",
                    (
                        "production",
                        month_now(),
                        40_000_000_000,
                        40_000_000_000,
                        "production",
                    ),
                )
            elif drift == "missing_id":
                db.execute(
                    "DELETE FROM requests WHERE id=?",
                    ("2ad399344ae54433b080c600156eefd6",),
                )
            elif drift == "missing_v2":
                db.execute(
                    "DELETE FROM records WHERE kind=? AND key=?",
                    ("m5_recovery_v2", "single_use"),
                )
            else:
                db.execute(
                    "INSERT INTO records(kind,key,data) VALUES(?,?,?)",
                    ("m5_openai_none_v3", "single_use", "broken"),
                )
        return result

    async def no_sdk(*_):
        raise AssertionError("SDK boundary must remain uncalled")

    monkeypatch.setattr(pilot, "preflight", preflight_then_change)
    monkeypatch.setattr(pilot, "execute_admitted", no_sdk)
    with pytest.raises(ValueError):
        await pilot.execute(none_plan)
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db:
        assert db.execute(
            "SELECT COUNT(*) FROM records WHERE kind=? AND key=?",
            ("m5_openai_none_v3", "single_use"),
        ).fetchone() == (int(drift == "concurrent_claim"),)


def test_none_prior_presence_money_and_header_share_the_read_snapshot(
    none_plan, monkeypatch
):
    connect = sqlite3.connect
    injected = False

    class Snapshot(sqlite3.Connection):
        def execute(self, statement, parameters=()):
            nonlocal injected
            cursor = super().execute(statement, parameters)
            if not injected and statement.startswith("SELECT 1 FROM sqlite_master"):
                injected = True
                assert self.in_transaction
                with (
                    closing(connect(none_plan.canonical_ledger_file)) as writer,
                    writer,
                ):
                    writer.execute(
                        "UPDATE requests SET reserved=15779451 WHERE id=?",
                        ("847b421069fc4e19aeab9a1a3385c8d8",),
                    )
            return cursor

    def readonly(*args, **kwargs):
        if args and "mode=ro" in str(args[0]):
            kwargs["factory"] = Snapshot
        return connect(*args, **kwargs)

    monkeypatch.setattr(pilot.sqlite3, "connect", readonly)
    result = pilot.preflight(none_plan)
    assert result["historical_nanousd"] == 5_162_800
    assert result["budget"]["spent"] == 863_500
    assert result["budget"]["reserved"] == 4_299_300
    with pytest.raises(ValueError, match="USD7"):
        pilot.preflight(none_plan)


async def test_none_probe_and_scored_profiles_reach_the_sdk_without_other_functional_changes(
    none_plan, monkeypatch
):
    from canary_brain import replay_cli

    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    calls, games = [], []
    reference = json.loads(REFERENCE.read_text())

    class Client:
        def __init__(self, **_):
            self.responses = SimpleNamespace(with_raw_response=self)
            self.count = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def create(self, **body):
            with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db:
                assert db.execute(
                    "SELECT COUNT(*) FROM records WHERE kind=? AND key=?",
                    ("m5_openai_none_v3", "single_use"),
                ).fetchone() == (1,)
            calls.append(body)
            self.count += 1
            assert body["max_output_tokens"] == 256
            name = "openai" if body["model"] == "canary-openai" else "gemini"
            if name == "openai":
                assert body["reasoning"] == {"effort": "none"}
            else:
                assert "reasoning" not in body
            if self.count == 3:
                await asyncio.sleep(2)
            options = body["tools"][0]["parameters"]["properties"]["candidate_id"][
                "enum"
            ]
            payload = {
                "id": "offline-none-request",
                "model": body["model"],
                "usage": {"input_tokens": 10, "output_tokens": 2},
                "output": [
                    {
                        "type": "function_call",
                        "name": "choose_action",
                        "arguments": json.dumps({"candidate_id": options[0]}),
                    }
                ],
            }
            headers = {
                "x-litellm-model-id": reference["gateway_profiles"][name][
                    "deployment_id"
                ],
                "x-litellm-call-id": "offline",
            }
            return SimpleNamespace(
                headers=headers,
                parse=lambda: SimpleNamespace(model_dump=lambda **_: payload),
            )

    async def game(experiment):
        participants = {p.name: p for p in experiment.participants}
        assert participants["openai"].gateway.decision_reasoning_effort == "none"
        assert participants["gemini"].gateway.decision_reasoning_effort is None
        assert experiment.seconds == 1800 and experiment.repetitions == 3
        assert experiment.seed == 42 and experiment.run_cap_nanousd == 1_000_000_000
        games.append(experiment)
        return {"offline_game_boundary": True}

    monkeypatch.setattr(replay_cli, "AsyncOpenAI", Client)
    monkeypatch.setattr(pilot, "run_attested_campaign", game)
    result = await pilot.execute(none_plan)
    assert len(calls) == 6 and len(games) == 1
    for name in ("openai", "gemini"):
        assert result["probes"][name]["qualification"]["policy"] == POLICY
        assert result["probes"][name]["qualification"]["accepted_for_game"] is True
        assert result["probes"][name]["qualification"]["unknown_requests"] == 1
        assert result["probes"][name]["qualification"]["financial_final"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("controller_profile", None),
        ("controller_profile", "different"),
        ("gateway_image", "sha256:" + "a" * 64),
        ("gateway_route_projection_sha256", "a" * 64),
        ("common_worker_python", "3.12.0"),
        ("openai_sdk", "3.42.0"),
        ("pydantic", "2.14.1"),
    ],
)
def test_none_profile_images_routes_and_dependencies_are_bound_to_the_reference(
    none_plan, field, value
):
    change(none_plan, none_plan.admission, lambda j: j.update({field: value}))
    with pytest.raises(ValueError, match="explicit-none"):
        pilot.preflight(none_plan)


def test_none_claim_rechecks_approved_input_bytes_after_preflight(none_plan):
    captured = pilot.capture_inputs(none_plan)
    admitted_result = pilot.preflight(none_plan, captured)
    change(none_plan, none_plan.campaign, lambda j: j.update(name="qa-raced-input"))
    with pytest.raises(ValueError, match="inputs changed"):
        pilot.claim_none_profile(none_plan, captured, admitted_result)
    with closing(sqlite3.connect(none_plan.canonical_ledger_file)) as db:
        assert db.execute(
            "SELECT COUNT(*) FROM records WHERE kind=? AND key=?",
            ("m5_openai_none_v3", "single_use"),
        ).fetchone() == (0,)


def test_none_fixture_identity_is_its_frozen_bytes_not_only_the_same_new_candidates(
    none_plan,
):
    change(
        none_plan,
        none_plan.decision_fixtures,
        lambda j: j[0]["observation"].update(sequence=99999),
    )
    with pytest.raises(ValueError, match="decision fixture bytes"):
        pilot.preflight(none_plan)


def test_none_reference_resource_is_loaded_from_the_same_frozen_export(
    none_plan, monkeypatch, tmp_path
):
    manifest = json.loads(none_plan.source_manifest.read_text())
    source = Path(manifest["source_path"])
    monkeypatch.setattr(
        pilot, "__file__", str(source / "deployment/brain/tools/m5_pilot.py")
    )
    monkeypatch.setattr(
        pilot.benchmark,
        "__file__",
        str(source / "deployment/brain/src/canary_brain/benchmark.py"),
    )
    monkeypatch.setattr(
        pilot.runtime,
        "__file__",
        str(source / "deployment/brain/src/canary_brain/runtime.py"),
    )
    pilot.assert_frozen_imports(manifest)
    asset = source / REFERENCE_PATH
    outside = tmp_path / "outside-reference.json"
    outside.write_bytes(asset.read_bytes())
    asset.unlink()
    asset.symlink_to(outside)
    with pytest.raises(ValueError, match="functional reference.*frozen source"):
        pilot.assert_frozen_imports(manifest)


@pytest.mark.parametrize("spent", [None, True, 52_800.0, "52800", -1])
def test_none_historical_amounts_cannot_be_coerced_or_forged(none_plan, spent):
    change(
        none_plan,
        none_plan.authorization,
        lambda j: j["historical_requests"][0].update(spent_nanousd=spent),
    )
    with pytest.raises(ValueError, match="explicit-none requires exact"):
        pilot.preflight(none_plan)
