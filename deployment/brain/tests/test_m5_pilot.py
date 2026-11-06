"""Admission, immutable inputs and shared accounting before any live M5 call."""

import asyncio
import hashlib
import json
import platform
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_protocol import observation

from canary_brain.benchmark import fixture_hash
from canary_brain.store import Store, month_now
from tools import m5_pilot as pilot


def write(path, value):
    path.write_text(json.dumps(value))
    return path


def approve_inputs(plan):
    gate = json.loads(plan.admission.read_text())
    gate.update(
        {
            "approved_inputs_sha256": {
                name: value
                for name, value in pilot.input_hashes(
                    pilot.capture_inputs(plan)
                ).items()
                if name != "admission"
            },
            "native_decoding_guarantees_equal": False,
            "comparison_scope": "configured_controller_stacks",
        }
    )
    write(plan.admission, gate)


def admit_short_deadline_policy(plan):
    """Freeze two 5s choices, a local choice, and the declared short deadlines."""
    fixtures = []
    for index, deadline in enumerate((5000, 5000, 5000, 1000, 1500, 1000)):
        snapshot = observation()
        snapshot["bot"]["id"] = 65001
        snapshot["sequence"] += index
        for action in snapshot["actions"]:
            action["ttl_ms"] = deadline
        if index == 2:
            snapshot["actions"] = snapshot["actions"][:1]
        fixtures.append({"observation": snapshot})
    write(plan.decision_fixtures, fixtures)
    admission = json.loads(plan.admission.read_text())
    admission["probe_outcome_policy"] = "short_deadline_performance_v1"
    write(plan.admission, admission)
    envelope = json.loads(plan.authorization.read_text())
    envelope["max_total_nanousd"] = 6_980_214_600
    write(plan.authorization, envelope)
    for path in plan.probe_workers.values():
        worker = json.loads(path.read_text())
        worker["decision_timeout"] = 10
        write(path, worker)
    approve_inputs(plan)


def fake_probe_sdk(monkeypatch, failure="timeout", mutate=None):
    """Replace only the SDK boundary; keep provider, recorder and ledger real."""
    from canary_brain import replay_cli

    calls = []

    class Client:
        def __init__(self, **_):
            self.responses = SimpleNamespace(with_raw_response=self)
            self.count = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def create(self, **body):
            self.count += 1
            calls.append(body)
            if self.count == 1 and failure == "long_timeout":
                await asyncio.sleep(6)
            if self.count == 1 and failure == "late_long_response":
                # Deliberately starve the loop to test a cooperative timer miss.
                time.sleep(5.02)  # noqa: ASYNC251
            if self.count == 3 and failure == "late_short_response":
                time.sleep(1.02)  # noqa: ASYNC251 - same blocking SDK regression
            if self.count == 3 and failure == "timeout":
                await asyncio.sleep(2)
            if self.count == 3 and failure == "auth":
                raise PermissionError("offline denied")
            if self.count == 3 and failure == "early_timeout":
                raise TimeoutError("offline early transport error")
            name = body["model"].removeprefix("alias-")
            options = body["tools"][0]["parameters"]["properties"]["candidate_id"][
                "enum"
            ]
            payload = {
                "id": "offline-provider-request",
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
                "x-litellm-model-id": "deployment-" + name,
                "x-litellm-call-id": "offline-gateway-request",
            }
            if self.count == 3 and failure == "usage":
                payload.pop("usage")
            if mutate is not None:
                mutate(self.count, payload, headers)
            return SimpleNamespace(
                headers=headers,
                parse=lambda: SimpleNamespace(model_dump=lambda **_: payload),
            )

    monkeypatch.setattr(replay_cli, "AsyncOpenAI", Client)
    return calls


@pytest.fixture
def admitted(tmp_path_factory, monkeypatch):
    root = tmp_path_factory.mktemp("pw")
    output = root / "p"
    ledger = root / "ledger.sqlite3"
    monkeypatch.setattr(pilot, "CANONICAL_LEDGER_FILE", ledger)
    store = Store(ledger)
    history = [
        {"id": "old-openai", "spent_nanousd": 52800},
        {"id": "old-gemini", "spent_nanousd": 161800},
    ]
    for row in history:
        store.reserve(row["id"], row["spent_nanousd"], month_now())
        store.settle(row["id"], row["spent_nanousd"])
    fixture = root / "fixture"
    fixture.mkdir()
    (fixture / "database.sql").write_text("-- isolated QA\n")
    write(
        fixture / "character.json",
        {
            "id": 65001,
            "level": 8,
            "experience": 4200,
            "posx": 100,
            "posy": 100,
            "posz": 7,
        },
    )
    world = root / "world.otbm"
    world.write_bytes(b"isolated map")
    credential = root / "client.env"
    credential.write_text("LITELLM_API_KEY=private-offline-fixture\n")
    credential.chmod(0o600)
    source = root / "source"
    files = {}
    for name in (
        "benchmark.py",
        "runtime.py",
        "provider.py",
        "gateway.py",
        "store.py",
        "recording.py",
        "replay_cli.py",
        "m5_pilot.py",
    ):
        relative = (
            "deployment/brain/"
            + ("tools/" if name == "m5_pilot.py" else "src/canary_brain/")
            + name
        )
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# frozen offline source fixture\n")
        files[relative] = pilot.file_hash(path)
    source_manifest = write(
        root / "source.json",
        {"revision": "a" * 40, "source_path": str(source), "files": files},
    )
    workers = {}
    participants = [{"name": "native", "kind": "native"}]
    for name in ("openai", "gemini"):
        gateway = {
            "base_url": "http://gateway:4000/v1",
            "alias": "alias-" + name,
            "effective_model": "model-" + name,
            "deployment_id": "deployment-" + name,
            "provider": name,
            "version": "1.108.0",
            "configuration_sha256": "b" * 64,
            "prices": {
                "version": "offline-fixture",
                "input_nanousd": 1,
                "cached_nanousd": 1,
                "cache_write_nanousd": 1,
                "output_nanousd": 2,
            },
        }
        participants.append({"name": name, "kind": "litellm", "gateway": gateway})
        workers[name] = write(
            root / (name + ".json"),
            {
                "provider": "litellm",
                "mode": "shadow",
                "socket_directory": str(output / "unused"),
                "state_file": str(output / name / "state.sqlite3"),
                "budget_file": str(ledger),
                "credential_file": str(credential),
                "bots": [65001],
                "monthly_usd": 50,
                "run_cap_nanousd": 490_000_000,
                "recording": {
                    "path": str(output / name / "replay.sqlite3"),
                    "namespace": "qa-" + name,
                },
                "gateway": gateway,
            },
        )
    campaign = write(
        root / "campaign.json",
        {
            "name": "qa-pilot",
            "output": str(output / "game"),
            "fixture": str(fixture),
            "world_map": str(world),
            "budget_file": str(ledger),
            "gateway_credential": str(credential),
            "game_image": "sha256:" + "1" * 64,
            "database_image": "sha256:" + "2" * 64,
            "bot_id": 65001,
            "participants": participants,
            "seconds": 1800,
            "repetitions": 3,
            "memory_mode": "frozen",
            "run_cap_nanousd": 1_000_000_000,
            "campaign_cap_nanousd": 6_000_000_000,
            "source_revision": "a" * 40,
            "expected_initial_sha256": fixture_hash(fixture, world),
        },
    )
    image = "sha256:" + "3" * 64
    admission = write(
        root / "admission.json",
        {
            "approved": True,
            "read_only_preparation": False,
            "required_gates": {key: True for key in pilot.GATES},
            "common_worker_image": image,
            "common_worker_python": platform.python_version(),
            "openai_sdk": pilot.importlib.metadata.version("openai"),
            "pydantic": pilot.importlib.metadata.version("pydantic"),
        },
    )
    envelope = write(
        root / "envelope.json",
        {
            "max_total_nanousd": 7_000_000_000,
            "canonical_monthly_cap_nanousd": 50_000_000_000,
            "canonical_authority": f"{pilot.CANONICAL_VOLUME}:{ledger}",
            "historical_requests": history,
            "scored": {
                "order": [
                    ["native", "openai", "gemini"],
                    ["openai", "gemini", "native"],
                    ["gemini", "native", "openai"],
                ]
            },
        },
    )
    observed = observation()
    observed["bot"]["id"] = 65001
    fixtures = write(
        root / "decisions.json",
        [{"observation": observed, "expected": "resupply"}],
    )
    admitted_inputs = json.loads(admission.read_text())
    admitted_inputs.update(
        {
            "approved_campaign_sha256": pilot.file_hash(campaign),
            "approved_decision_fixtures_sha256": pilot.file_hash(fixtures),
            "source_revision": "a" * 40,
        }
    )
    write(admission, admitted_inputs)
    monkeypatch.setattr(
        pilot,
        "container_identity",
        lambda: (
            image,
            [
                {
                    "Type": "volume",
                    "Name": pilot.CANONICAL_VOLUME,
                    "Destination": str(ledger.parent),
                    "RW": True,
                }
            ],
        ),
    )
    plan = pilot.Plan(
        output=output,
        campaign=campaign,
        admission=admission,
        authorization=envelope,
        source_manifest=source_manifest,
        decision_fixtures=fixtures,
        probe_workers=workers,
        worker_image=image,
        canonical_ledger_file=ledger,
    )
    approve_inputs(plan)
    return plan


def test_preflight_accepts_pinned_single_authority_without_creating_output(admitted):
    before = admitted.canonical_ledger_file.read_bytes()
    result = pilot.preflight(admitted)
    assert result["accepted"] and result["historical_nanousd"] == 214600
    assert (
        result["new_worst_case_nanousd"] + result["historical_nanousd"] < 7_000_000_000
    )
    assert result["order"][-1] == ["gemini", "native", "openai"]
    assert not admitted.output.exists()
    assert admitted.canonical_ledger_file.read_bytes() == before


def test_preflight_accepts_immutable_manifest_digest(admitted):
    campaign = json.loads(admitted.campaign.read_text())
    campaign["game_image"] = "registry.example/game@sha256:" + "3" * 64
    write(admitted.campaign, campaign)
    gate = json.loads(admitted.admission.read_text())
    gate["approved_campaign_sha256"] = pilot.file_hash(admitted.campaign)
    write(admitted.admission, gate)
    approve_inputs(admitted)

    assert pilot.preflight(admitted)["accepted"] is True


def test_missing_ledger_is_not_recreated(admitted):
    admitted.canonical_ledger_file.unlink()
    with pytest.raises(ValueError, match="must already exist"):
        pilot.preflight(admitted)
    assert not admitted.canonical_ledger_file.exists()
    assert not admitted.output.exists()


def test_coherently_repointed_backup_in_same_volume_is_not_authority(admitted):
    backup = admitted.canonical_ledger_file.with_name("state-backup.sqlite3")
    backup.write_bytes(admitted.canonical_ledger_file.read_bytes())
    changed = admitted.model_copy(update={"canonical_ledger_file": backup})
    campaign = json.loads(changed.campaign.read_text())
    campaign["budget_file"] = str(backup)
    write(changed.campaign, campaign)
    for path in changed.probe_workers.values():
        config = json.loads(path.read_text())
        config["budget_file"] = str(backup)
        write(path, config)
    envelope = json.loads(changed.authorization.read_text())
    envelope["canonical_authority"] = f"{pilot.CANONICAL_VOLUME}:{backup}"
    write(changed.authorization, envelope)
    approve_inputs(changed)
    with pytest.raises(ValueError, match="canonical monthly ledger"):
        pilot.preflight(changed)
    assert not changed.output.exists()


def test_unaccepted_gate_blocks_before_container_or_financial_reads(
    admitted, monkeypatch
):
    value = json.loads(admitted.admission.read_text())
    value["required_gates"]["routing_immutable_before_upstream"] = False
    write(admitted.admission, value)
    monkeypatch.setattr(
        pilot, "container_identity", lambda: pytest.fail("must not inspect container")
    )
    with pytest.raises(ValueError, match="root admission"):
        pilot.preflight(admitted)


def test_copied_ledger_mount_is_rejected(admitted, monkeypatch):
    monkeypatch.setattr(
        pilot,
        "container_identity",
        lambda: (
            admitted.worker_image,
            [
                {
                    "Type": "bind",
                    "Name": "copied-budget",
                    "Destination": str(admitted.canonical_ledger_file.parent),
                    "RW": True,
                }
            ],
        ),
    )
    with pytest.raises(ValueError, match="canonical Docker volume"):
        pilot.preflight(admitted)


def test_changed_source_or_reused_output_blocks_execution(admitted):
    source = json.loads(admitted.source_manifest.read_text())
    target = Path(source["source_path"]) / next(iter(source["files"]))
    target.write_text("changed source")
    with pytest.raises(ValueError, match="frozen source bytes"):
        pilot.preflight(admitted)
    admitted.output.mkdir()
    (admitted.output / "execution-started.json").write_text("{}")
    with pytest.raises(ValueError, match="new or empty"):
        pilot.preflight(admitted)


def test_multiple_probe_bots_cannot_multiply_the_model_cap(admitted):
    rows = json.loads(admitted.decision_fixtures.read_text())
    other = observation()
    other["bot"]["id"] = 8
    rows.append({"observation": other})
    write(admitted.decision_fixtures, rows)
    gate = json.loads(admitted.admission.read_text())
    gate["approved_decision_fixtures_sha256"] = pilot.file_hash(
        admitted.decision_fixtures
    )
    write(admitted.admission, gate)
    approve_inputs(admitted)
    with pytest.raises(ValueError, match="one recorded bot"):
        pilot.preflight(admitted)


def test_approval_cannot_be_reused_after_changing_a_campaign(admitted):
    campaign = json.loads(admitted.campaign.read_text())
    campaign["name"] = "another-campaign"
    write(admitted.campaign, campaign)
    with pytest.raises(ValueError, match="bound to these exact inputs"):
        pilot.preflight(admitted)


def test_unlisted_source_module_cannot_enter_frozen_execution(admitted):
    source = Path(json.loads(admitted.source_manifest.read_text())["source_path"])
    (source / "deployment/brain/src/canary_brain/controller.py").write_text(
        "# unlisted source\n"
    )
    with pytest.raises(ValueError, match="omits Python modules"):
        pilot.preflight(admitted)


def test_ledger_export_includes_unplanned_namespace_but_not_unrelated_rows(admitted):
    store = Store(admitted.canonical_ledger_file)
    store.reserve("unplanned", 400, month_now(), run_id="qa-pilot:unplanned:99")
    store.reserve("production", 300, month_now(), run_id="production-lifetime")
    result = pilot.ledger_export(admitted)
    assert {row["id"] for row in result["requests"]} == {
        "old-openai",
        "old-gemini",
        "unplanned",
    }
    assert result["budget"]["spent"] == 214600
    assert result["budget"]["reserved"] == 700
    assert result["snapshot_utc"].endswith("+00:00")
    assert result["month"] == month_now()


def test_prior_additional_costs_also_consume_the_pilot_envelope(admitted):
    Store(admitted.canonical_ledger_file).reserve(
        "prior", 40_000_000, month_now(), run_id="prior-probe"
    )
    envelope = json.loads(admitted.authorization.read_text())
    envelope["additional_cost_run_ids"] = ["prior-probe"]
    write(admitted.authorization, envelope)
    approve_inputs(admitted)
    with pytest.raises(ValueError, match="insufficient room inside USD7"):
        pilot.preflight(admitted)


def test_reusing_a_charged_campaign_name_is_rejected_even_in_a_new_directory(admitted):
    Store(admitted.canonical_ledger_file).reserve(
        "old-attempt", 1000, month_now(), run_id="qa-pilot:openai:0"
    )
    with pytest.raises(ValueError, match="campaign identity already"):
        pilot.preflight(admitted)


def test_canonical_volume_lease_blocks_another_output_and_releases_on_failure(admitted):
    with pytest.raises(RuntimeError), pilot.pilot_lease(admitted.canonical_ledger_file):
        with (
            pytest.raises(ValueError, match="another M5 orchestrator"),
            pilot.pilot_lease(admitted.canonical_ledger_file),
        ):
            pytest.fail("lease must be exclusive")
        raise RuntimeError("simulated stop")
    with pilot.pilot_lease(admitted.canonical_ledger_file):
        pass


async def test_conformance_failure_blocks_campaign_and_preserves_result(
    admitted, monkeypatch
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    calls = []

    async def fail(args):
        calls.append(args)
        return {"decisions": [{"valid": False}], "runs": []}

    async def forbidden(_):
        pytest.fail("failed conformance must not start game")

    monkeypatch.setattr(pilot, "decision_fixtures", fail)
    monkeypatch.setattr(pilot, "run_attested_campaign", forbidden)
    with pytest.raises(ValueError, match="conformance failed"):
        await pilot.execute(admitted)
    assert len(calls) == 1
    result = json.loads((admitted.output / "execution-result.json").read_text())
    assert result["error_type"] == "ValueError" and result["campaign"] is None
    assert (admitted.output / "inputs/campaign.json").is_file()
    with pytest.raises(ValueError, match="new or empty"):
        await pilot.execute(admitted)


async def test_attested_hook_is_common_and_restored_after_failure(
    admitted, monkeypatch
):
    experiment = pilot.benchmark.Experiment.model_validate_json(
        admitted.campaign.read_text()
    )
    original_fixture = pilot.benchmark.DockerFixture
    original_run = pilot.benchmark.run
    seen = []

    async def inspect_and_fail(config, live):
        assert live
        for participant in config.participants:
            harness = pilot.benchmark.DockerFixture(
                config,
                config.output / f"{participant.name}-0",
                hashlib.sha256(
                    f"{config.name}:{participant.name}:0".encode()
                ).hexdigest(),
            )
            harness.prepare(participant)
            compose = json.loads(harness.compose.read_text())
            seen.append(
                (compose["networks"], compose["services"]["game"]["volumes"][-1])
            )
        raise RuntimeError("offline simulated failure")

    monkeypatch.setattr(pilot.benchmark, "run_campaign", inspect_and_fail)
    with pytest.raises(RuntimeError, match="offline simulated failure"):
        await pilot.run_attested_campaign(experiment)
    assert len(seen) == 3 and all(
        row[0] == {"default": {"internal": True}} and row[1].endswith(":/m5")
        for row in seen
    )
    assert pilot.benchmark.DockerFixture is original_fixture
    assert pilot.benchmark.run is original_run


async def test_deadline_is_a_retained_performance_outcome_needing_root_review(
    admitted, monkeypatch
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    calls = []

    async def late(args):
        calls.append(args)
        Store(admitted.canonical_ledger_file).reserve(
            "late", 1000, month_now(), run_id="decisions:late:65001"
        )
        return {
            "decisions": [{"valid": False, "error": "TimeoutError"}],
            "runs": ["decisions:late:65001"],
        }

    async def forbidden(_):
        pytest.fail("deadline outcome needs root review before a scored run")

    monkeypatch.setattr(pilot, "decision_fixtures", late)
    monkeypatch.setattr(pilot, "run_attested_campaign", forbidden)
    with pytest.raises(ValueError, match="conformance failed"):
        await pilot.execute(admitted)
    result = json.loads((admitted.output / "execution-result.json").read_text())
    gate = result["probes"]["openai"]["qualification"]
    assert gate["late"] == gate["unknown_requests"] == 1
    assert gate["unknown_nanousd"] == 1000 and gate["root_review_required"]
    assert gate["failure_interpretation"] == "deadline_performance"
    assert len(calls) == 1
    ledger = json.loads((admitted.output / "ledger.json").read_text())
    assert (
        next(row for row in ledger["requests"] if row["id"] == "late")["spent"] is None
    )


async def test_admitted_short_deadlines_and_causal_backoff_reach_campaign_once(
    admitted, monkeypatch
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    admit_short_deadline_policy(admitted)
    calls = fake_probe_sdk(monkeypatch)
    campaigns = []

    async def game(experiment):
        campaigns.append(experiment)
        return {"offline": True}

    monkeypatch.setattr(pilot, "run_attested_campaign", game)
    result = await pilot.execute(admitted)
    assert len(campaigns) == 1 and len(calls) == 6
    assert campaigns[0].name == "qa-pilot" and campaigns[0].repetitions == 3
    for name in ("openai", "gemini"):
        gate = result["probes"][name]["qualification"]
        assert gate["accepted_for_game"] is True
        assert gate["long_valid"] == 2
        assert gate["late"] == 1 and gate["causal_backoff"] == 2
        assert gate["unknown_requests"] == 1 and gate["unknown_nanousd"] > 0
        assert gate["model_opportunities"] == 5 and gate["ledger_requests"] == 3
        assert gate["technical_invalid"] == 0
        assert [row["valid"] for row in result["probes"][name]["decisions"]] == [
            True,
            True,
            True,
            False,
            False,
            False,
        ]
    ledger = json.loads((admitted.output / "ledger.json").read_text())
    assert len([row for row in ledger["requests"] if row["spent"] is None]) == 2
    assert ledger["budget"]["reserved"] > 0
    with pytest.raises(ValueError, match="new or empty"):
        await pilot.execute(admitted)
    assert len(calls) == 6


@pytest.mark.parametrize("failure", ["usage", "auth"])
async def test_short_deadline_policy_keeps_observed_technical_failures_blocking(
    admitted, monkeypatch, failure
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    admit_short_deadline_policy(admitted)
    calls = fake_probe_sdk(monkeypatch, failure=failure)

    async def forbidden(_):
        pytest.fail("observed technical failure must block game")

    monkeypatch.setattr(pilot, "run_attested_campaign", forbidden)
    with pytest.raises(ValueError, match="technical or unreconciled"):
        await pilot.execute(admitted)
    assert len(calls) == 3
    result = json.loads((admitted.output / "execution-result.json").read_text())
    assert set(result["probes"]) == {"openai"}
    assert result["probes"]["openai"]["qualification"]["accepted_for_game"] is False
    ledger = json.loads((admitted.output / "ledger.json").read_text())
    assert len([row for row in ledger["requests"] if row["spent"] is None]) == 1


def test_short_deadline_envelope_retains_prior_unknown_liability(admitted):
    admit_short_deadline_policy(admitted)
    Store(admitted.canonical_ledger_file).reserve(
        "prior-unknown", 1, month_now(), run_id="prior-probe"
    )
    envelope = json.loads(admitted.authorization.read_text())
    envelope["additional_cost_run_ids"] = ["prior-probe"]
    write(admitted.authorization, envelope)
    approve_inputs(admitted)
    with pytest.raises(ValueError, match="prospective complete liability envelope"):
        pilot.preflight(admitted)
    assert not admitted.output.exists()


@pytest.mark.parametrize(
    "fault",
    [
        "route",
        "schema",
        "long_timeout",
        "late_long_response",
        "late_short_response",
        "early_timeout",
    ],
)
async def test_deadline_policy_cannot_waive_long_or_response_contract_failures(
    admitted, monkeypatch, fault
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    admit_short_deadline_policy(admitted)

    def mutate(count, payload, headers):
        if count == 1 and fault == "route":
            headers["x-litellm-model-id"] = "another-deployment"
        if count == 3 and fault == "schema":
            payload["output"][0]["arguments"] = '{"candidate_id":"not-offered"}'

    fake_probe_sdk(monkeypatch, failure=fault, mutate=mutate)

    async def forbidden(_):
        pytest.fail("a 5s deadline or observed contract/route failure blocks game")

    monkeypatch.setattr(pilot, "run_attested_campaign", forbidden)
    with pytest.raises(ValueError, match="technical or unreconciled"):
        await pilot.execute(admitted)
    result = json.loads((admitted.output / "execution-result.json").read_text())
    assert result["campaign"] is None
    assert result["probes"]["openai"]["qualification"]["accepted_for_game"] is False
    if fault in {"late_long_response", "late_short_response"}:
        assert (
            result["probes"]["openai"]["qualification"]["rejection_reason"]
            == "positive_timing_unqualified"
        )


@pytest.mark.parametrize(
    "fault",
    ["unknown", "relabeled_usage", "gap", "relabeled_skipped", "relabeled_schema"],
)
async def test_deadline_policy_reconciles_evidence_instead_of_trusting_error_labels(
    admitted, monkeypatch, fault
):
    from canary_brain.recording import RecordingStore

    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    admit_short_deadline_policy(admitted)

    def invalid_choice(count, payload, _):
        if count == 3 and fault == "relabeled_schema":
            payload["output"][0]["arguments"] = '{"candidate_id":"not-offered"}'

    fake_probe_sdk(
        monkeypatch,
        failure=(
            "usage"
            if fault == "relabeled_usage"
            else "none"
            if fault == "relabeled_schema"
            else "timeout"
        ),
        mutate=invalid_choice,
    )
    actual = pilot.decision_fixtures

    async def altered(args):
        probe = await actual(args)
        if fault == "unknown":
            Store(admitted.canonical_ledger_file).reserve(
                "unattributed-unknown", 1, month_now(), run_id=probe["runs"][0]
            )
        elif fault == "relabeled_usage":
            probe["decisions"][3]["error"] = "TimeoutError"
        elif fault == "relabeled_skipped":
            probe["decisions"][4]["valid"] = True
            probe["decisions"][4]["choice"] = "continue"
        elif fault == "relabeled_schema":
            probe["decisions"][3].update(valid=True, choice="continue")
            probe["decisions"][3].pop("error")
        else:
            config = pilot.runtime.Configuration.model_validate_json(
                args.worker_config.read_text()
            )
            RecordingStore(config.recording.path).append(
                {
                    "run": probe["runs"][0],
                    "key": "lost-evidence",
                    "segment": "offline",
                    "t_ms": 0,
                    "wall": 1,
                    "kind": "gap",
                    "data": {"reason": "offline-loss"},
                }
            )
        return probe

    monkeypatch.setattr(pilot, "decision_fixtures", altered)

    async def forbidden(_):
        pytest.fail("unreconciled evidence must not start game")

    monkeypatch.setattr(pilot, "run_attested_campaign", forbidden)
    with pytest.raises(ValueError, match="technical or unreconciled"):
        await pilot.execute(admitted)
    result = json.loads((admitted.output / "execution-result.json").read_text())
    assert result["campaign"] is None
    assert result["probes"]["openai"]["qualification"]["evidence_reconciled"] is False


@pytest.mark.parametrize("change", ["deadline", "policy", "envelope"])
def test_prospective_deadline_policy_is_explicit_and_cannot_expand_bounds(
    admitted, change
):
    admit_short_deadline_policy(admitted)
    if change == "deadline":
        path = admitted.probe_workers["openai"]
        config = json.loads(path.read_text())
        config["decision_timeout"] = 1.2
        write(path, config)
    elif change == "policy":
        document = json.loads(admitted.admission.read_text())
        document["probe_outcome_policy"] = "accept-every-error"
        write(admitted.admission, document)
    else:
        envelope = json.loads(admitted.authorization.read_text())
        envelope["max_total_nanousd"] = 7_000_000_000
        write(admitted.authorization, envelope)
    approve_inputs(admitted)
    with pytest.raises(ValueError):
        pilot.preflight(admitted)
    assert not admitted.output.exists()


async def test_prospective_deadline_policy_also_accepts_all_five_responses(
    admitted, monkeypatch
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    admit_short_deadline_policy(admitted)
    calls = fake_probe_sdk(monkeypatch, failure="none")

    async def game(_):
        return {"offline": True}

    monkeypatch.setattr(pilot, "run_attested_campaign", game)
    result = await pilot.execute(admitted)
    assert len(calls) == 10
    for name in ("openai", "gemini"):
        gate = result["probes"][name]["qualification"]
        assert gate["financial_final"] and gate["evidence_reconciled"]
        assert gate["short_contract_coverage_complete"] and gate["long_valid"] == 2
        assert gate["unknown_requests"] == gate["late"] == gate["causal_backoff"] == 0
        assert gate["ledger_requests"] == 5


async def test_deadline_evidence_includes_reservation_time_before_the_request_clock(
    admitted, monkeypatch
):
    from canary_brain.recording import ReplayReader

    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    admit_short_deadline_policy(admitted)
    fake_probe_sdk(monkeypatch)
    reserve = Store.reserve
    counts = {}

    def slow_reservation(store, identity, amount, month, endpoint="", **kwargs):
        run = kwargs.get("run_id")
        counts[run] = counts.get(run, 0) + 1
        if endpoint == "responses" and counts[run] == 3:
            time.sleep(0.12)
        return reserve(store, identity, amount, month, endpoint, **kwargs)

    monkeypatch.setattr(Store, "reserve", slow_reservation)

    async def game(_):
        return {"offline": True}

    monkeypatch.setattr(pilot, "run_attested_campaign", game)
    result = await pilot.execute(admitted)
    for name, path in admitted.probe_workers.items():
        probe = result["probes"][name]
        assert probe["qualification"]["accepted_for_game"]
        assert probe["decisions"][3]["elapsed_ms"] >= 1000
        worker = json.loads(path.read_text())
        failures = [
            event["data"]
            for event in ReplayReader(Path(worker["recording"]["path"])).all_events(
                probe["runs"][0]
            )
            if event["kind"] == "request" and event["data"].get("phase") == "failed"
        ]
        assert len(failures) == 1
        assert 0 <= failures[0]["elapsed_ms"] < 1000


async def test_actual_probe_spend_above_cap_blocks_without_releasing_its_liability(
    admitted, monkeypatch
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)
    admit_short_deadline_policy(admitted)

    def overrun(count, payload, _):
        if count == 1:
            payload["usage"]["input_tokens"] = 490_000_001

    fake_probe_sdk(monkeypatch, failure="none", mutate=overrun)

    async def forbidden(_):
        pytest.fail("actual probe spend above USD0.49 cannot admit game")

    monkeypatch.setattr(pilot, "run_attested_campaign", forbidden)
    with pytest.raises(ValueError, match="technical or unreconciled"):
        await pilot.execute(admitted)
    ledger = json.loads((admitted.output / "ledger.json").read_text())
    assert any(row["spent"] == 490_000_005 for row in ledger["requests"])


@pytest.mark.parametrize("which", ["campaign", "openai"])
def test_config_mutation_during_preflight_cannot_capture_unvalidated_new_hash(
    admitted, monkeypatch, which
):
    identity = pilot.container_identity

    def mutate():
        path = (
            admitted.campaign if which == "campaign" else admitted.probe_workers[which]
        )
        value = json.loads(path.read_text())
        value.update(
            {"run_cap_nanousd": 2_000_000_000, "campaign_cap_nanousd": 12_000_000_000}
            if which == "campaign"
            else {"decision_timeout": 30}
        )
        write(path, value)
        return identity()

    monkeypatch.setattr(pilot, "container_identity", mutate)
    with pytest.raises(ValueError, match="inputs changed during read-only preflight"):
        pilot.preflight(admitted)
    assert not admitted.output.exists()


def test_source_rehash_without_new_root_admission_is_rejected(admitted):
    manifest = json.loads(admitted.source_manifest.read_text())
    name = next(iter(manifest["files"]))
    target = Path(manifest["source_path"]) / name
    target.write_text("# changed after approval\n")
    manifest["files"][name] = pilot.file_hash(target)
    write(admitted.source_manifest, manifest)
    with pytest.raises(ValueError, match="bound to these exact inputs"):
        pilot.preflight(admitted)


def test_file_mount_shadowing_cannot_disguise_a_copied_ledger(admitted, monkeypatch):
    image, mounts = pilot.container_identity()
    mounts.append(
        {"Type": "bind", "Destination": str(admitted.canonical_ledger_file), "RW": True}
    )
    monkeypatch.setattr(pilot, "container_identity", lambda: (image, mounts))
    with pytest.raises(ValueError, match="shadowed"):
        pilot.preflight(admitted)


async def test_execution_uses_validated_bytes_even_when_original_paths_change(
    admitted, monkeypatch
):
    def change_originals(_):
        value = json.loads(admitted.campaign.read_text())
        value.update(
            {"run_cap_nanousd": 2_000_000_000, "campaign_cap_nanousd": 12_000_000_000}
        )
        write(admitted.campaign, value)
        value = json.loads(admitted.probe_workers["openai"].read_text())
        value["decision_timeout"] = 30
        write(admitted.probe_workers["openai"], value)
        write(admitted.decision_fixtures, [])

    async def probe(args):
        config = json.loads(args.worker_config.read_text())
        assert config.get("decision_timeout", 1.2) == 1.2
        assert len(json.loads(args.fixtures.read_text())) == 1
        name = config["gateway"]["provider"]
        run = "decisions:captured:" + name
        store = Store(admitted.canonical_ledger_file)
        store.reserve(name, 10, month_now(), run_id=run)
        store.settle(name, 10)
        return {"runs": [run], "decisions": [{"valid": True}]}

    async def game(config):
        assert config.run_cap_nanousd == 1_000_000_000
        assert config.campaign_cap_nanousd == 6_000_000_000
        return {"completed": True}

    monkeypatch.setattr(pilot, "assert_frozen_imports", change_originals)
    monkeypatch.setattr(pilot, "decision_fixtures", probe)
    monkeypatch.setattr(pilot, "run_attested_campaign", game)
    result = await pilot.execute(admitted)
    assert result["campaign"]["completed"]
    assert (
        json.loads((admitted.output / "inputs/campaign.json").read_text())[
            "run_cap_nanousd"
        ]
        == 1_000_000_000
    )


async def test_observer_failure_is_not_silently_qualified_as_completed(
    admitted, monkeypatch
):
    state = admitted.output / "worker.sqlite3"
    state.parent.mkdir()
    joined = []

    async def worker(_, stop):
        await stop.wait()
        joined.append(True)

    async def broken(*args):
        raise RuntimeError("offline status query failure")

    async def campaign(config, live):
        await pilot.benchmark.run(SimpleNamespace(state_file=state), asyncio.Event())
        return {"completed": True}

    monkeypatch.setattr(pilot.runtime, "run", worker)
    monkeypatch.setattr(pilot, "observe_status", broken)
    monkeypatch.setattr(pilot.benchmark, "run_campaign", campaign)
    config = pilot.benchmark.Experiment.model_validate_json(
        admitted.campaign.read_text()
    )
    with pytest.raises(RuntimeError, match="status observer failed"):
        await pilot.run_attested_campaign(config)
    assert joined == [True]
    assert (
        json.loads((state.parent / "status-observer-error.json").read_text())[
            "error_type"
        ]
        == "RuntimeError"
    )


async def test_mixed_deadline_and_technical_failures_remain_distinct(
    admitted, monkeypatch
):
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)

    async def mixed(_):
        return {
            "runs": [],
            "decisions": [
                {"valid": False, "error": "TimeoutError"},
                {"valid": False, "error": "ValueError"},
            ],
        }

    monkeypatch.setattr(pilot, "decision_fixtures", mixed)
    with pytest.raises(ValueError, match="conformance failed"):
        await pilot.execute(admitted)
    result = json.loads((admitted.output / "execution-result.json").read_text())
    qualification = result["probes"]["openai"]["qualification"]
    assert qualification["late"] == qualification["technical_invalid"] == 1
    assert qualification["failure_interpretation"] == "mixed"


async def test_attestation_failure_preserves_admitted_bytes_results_and_releases_lease(
    admitted, monkeypatch
):
    from test_m5_attestations import Docker

    before = pilot.capture_inputs(admitted)
    engine = Docker()
    monkeypatch.setattr(pilot.subprocess, "check_output", engine.query)
    monkeypatch.setattr(
        pilot.benchmark.DockerFixture,
        "command",
        lambda own, *args, **kwargs: engine.command(own, *args, **kwargs),
    )
    monkeypatch.setattr(pilot, "assert_frozen_imports", lambda _: None)

    async def probe(args):
        name = json.loads(args.worker_config.read_text())["gateway"]["provider"]
        store = Store(admitted.canonical_ledger_file)
        store.reserve(name, 10, month_now(), run_id="decisions:attestation:" + name)
        store.settle(name, 10)
        return {
            "runs": ["decisions:attestation:" + name],
            "decisions": [{"valid": True}],
        }

    async def campaign(config, live):
        run_id = f"{config.name}:native:0"
        trial = pilot.benchmark.DockerFixture(
            config,
            config.output / "native-0",
            hashlib.sha256(run_id.encode()).hexdigest(),
        )
        config.output.mkdir()
        trial.prepare(config.participants[0])
        trial.start_database()
        try:
            trial.start_game()
            engine.leftover = engine.container(trial, "game", "running")
        finally:
            trial.close()

    monkeypatch.setattr(pilot, "decision_fixtures", probe)
    monkeypatch.setattr(pilot.benchmark, "run_campaign", campaign)
    with pytest.raises(RuntimeError, match="cleanup could not be verified"):
        await pilot.execute(admitted)
    for name, payload in before.items():
        assert (admitted.output / "inputs" / (name + ".json")).read_bytes() == payload
    result = json.loads((admitted.output / "execution-result.json").read_text())
    assert result["error_type"] == "RuntimeError"
    assert (admitted.output / "ledger.json").is_file()
    with pilot.pilot_lease(admitted.canonical_ledger_file):
        pass
