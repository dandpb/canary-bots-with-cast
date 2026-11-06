"""Admission, immutable inputs and shared accounting before any live M5 call."""

import json
import platform
from pathlib import Path

import pytest
from test_protocol import observation

from canary_brain.benchmark import fixture_hash
from canary_brain.store import Store, month_now
from tools import m5_pilot as pilot


def write(path, value):
    path.write_text(json.dumps(value))
    return path


@pytest.fixture
def admitted(tmp_path_factory, monkeypatch):
    root = tmp_path_factory.mktemp("pw")
    output = root / "p"
    ledger = root / "ledger.sqlite3"
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
    return pilot.Plan(
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


def test_missing_ledger_is_not_recreated(admitted):
    admitted.canonical_ledger_file.unlink()
    with pytest.raises(ValueError, match="must already exist"):
        pilot.preflight(admitted)
    assert not admitted.canonical_ledger_file.exists()
    assert not admitted.output.exists()


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
    with pytest.raises(ValueError, match="insufficient room inside USD7"):
        pilot.preflight(admitted)


def test_reusing_a_charged_campaign_name_is_rejected_even_in_a_new_directory(admitted):
    Store(admitted.canonical_ledger_file).reserve(
        "old-attempt", 1000, month_now(), run_id="qa-pilot:openai:0"
    )
    with pytest.raises(ValueError, match="campaign identity already"):
        pilot.preflight(admitted)


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
                config, admitted.output / participant.name, participant.name
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
