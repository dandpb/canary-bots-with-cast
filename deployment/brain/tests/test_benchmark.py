import asyncio
import json
import time
from types import SimpleNamespace

import pytest
from test_gateway import gateway
from test_protocol import observation

from canary_brain.benchmark import (
    DockerFixture,
    Experiment,
    Participant,
    campaign_lease,
    demo,
    evaluate_decisions,
    fixture_hash,
    preflight,
    run_campaign,
)
from canary_brain.gateway_policy import validate_policy
from canary_brain.recording import Manifest, RecordingStore, ReplayReader, digest
from canary_brain.replay import campaign, export_report
from canary_brain.store import USD, Store, month_now
from canary_brain.testing import FakeProvider


def test_failed_docker_diagnostics_are_retained_with_credentials_redacted(
    tmp_path, monkeypatch
):
    config = experiment(tmp_path)
    harness = DockerFixture(config, config.output / "native-0", "qa-only")
    harness.directory.parent.mkdir()
    harness.prepare(config.participants[0])
    private_value = harness.env_file.read_text().splitlines()[0].split("=", 1)[1]
    monkeypatch.setattr(
        "canary_brain.benchmark.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1, stdout="failed", stderr="private: " + private_value
        ),
    )
    with pytest.raises(RuntimeError, match="isolated Docker"):
        harness.command("up")
    diagnostics = (harness.directory / "command-errors.log").read_text()
    assert "[redacted]" in diagnostics and private_value not in diagnostics


@pytest.mark.parametrize(
    ("original", "status"),
    [
        (RuntimeError("database startup failed"), "failed"),
        (asyncio.CancelledError("operator stop"), "interrupted"),
    ],
)
async def test_cleanup_failure_preserves_original_error_and_marks_gap(
    tmp_path, monkeypatch, original, status
):
    config = experiment(tmp_path)

    class Harness(DockerFixture):
        def start_database(self):
            raise original

        def close(self):
            raise RuntimeError("docker down failed")

    monkeypatch.setattr("canary_brain.benchmark.DockerFixture", Harness)
    with pytest.raises(type(original)) as raised:
        await run_campaign(config, live=True)
    assert raised.value is original
    assert any("cleanup also failed" in note for note in raised.value.__notes__)
    reader = ReplayReader(config.output / "recording.sqlite3")
    run = reader.run("qa:native:0")
    assert run["status"] == status
    assert run["incomplete"] is True
    assert any(
        event["kind"] == "gap" and event["data"]["reason"] == "cleanup_unverified"
        for event in reader.events("qa:native:0")
    )


@pytest.mark.parametrize("teardown_cancel", [False, True])
async def test_cleanup_failure_cannot_certify_completion_or_mask_teardown_cancel(
    tmp_path, monkeypatch, teardown_cancel
):
    config = experiment(tmp_path)

    class Harness(DockerFixture):
        def start_database(self):
            pass

        def character(self):
            return json.loads((config.fixture / "character.json").read_text())

        def start_game(self):
            pass

        def stop_game(self):
            pass

        def close(self):
            raise RuntimeError("docker down failed")

    async def worker(configuration, _stopped):
        (configuration.socket_directory / "worker.sock").touch()
        state = Store(configuration.state_file)
        state.put("run_clock", "start", {"monotonic": time.monotonic() - 11})
        state.put(
            "run_stop",
            "end",
            {"reason": "completed", "elapsed_seconds": 11, "observed_seconds": 11},
        )
        for index, milliseconds in enumerate((0, 11000)):
            RecordingStore(configuration.recording.path).append(
                {
                    "run": configuration.recording.manifests[0].run_id,
                    "key": str(index),
                    "segment": "fixture",
                    "t_ms": milliseconds,
                    "wall": time.time(),
                    "kind": "sample",
                    "data": observation(),
                }
            )

    monkeypatch.setattr("canary_brain.benchmark.DockerFixture", Harness)
    monkeypatch.setattr("canary_brain.benchmark.run", worker)
    teardown_error = asyncio.CancelledError("teardown cancelled")
    if teardown_cancel:
        actual_gather = asyncio.gather
        calls = 0

        async def cancel_gather(*tasks, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise teardown_error
            return await actual_gather(*tasks, **kwargs)

        monkeypatch.setattr("canary_brain.benchmark.asyncio.gather", cancel_gather)

    expected = asyncio.CancelledError if teardown_cancel else RuntimeError
    with pytest.raises(expected) as raised:
        await run_campaign(config, live=True)
    if teardown_cancel:
        assert raised.value is teardown_error
        assert any("cleanup also failed" in note for note in teardown_error.__notes__)
    else:
        assert str(raised.value) == "docker down failed"
    reader = ReplayReader(config.output / "recording.sqlite3")
    run = reader.run("qa:native:0")
    assert run["status"] == ("interrupted" if teardown_cancel else "failed")
    assert run["incomplete"] is True
    assert any(
        event["kind"] == "gap" and event["data"]["reason"] == "cleanup_unverified"
        for event in reader.events("qa:native:0")
    )


def test_service_logs_are_redacted_and_retained_before_container_teardown(
    tmp_path, monkeypatch
):
    config = experiment(tmp_path)
    harness = DockerFixture(config, config.output / "native-0", "qa-only")
    harness.prepare(config.participants[0])
    private_value = harness.env_file.read_text().splitlines()[0].split("=", 1)[1]
    calls = []

    def command(*args, **kwargs):
        calls.append(args)
        return "database failure " + private_value

    monkeypatch.setattr(harness, "command", command)
    harness.started = True
    harness.close()
    logs = (harness.directory / "services.log").read_text()
    assert "[redacted]" in logs and private_value not in logs
    assert calls[0][0] == "logs" and calls[1][0] == "down"


def test_teardown_still_runs_when_diagnostic_storage_fails(tmp_path, monkeypatch):
    config = experiment(tmp_path)
    harness = DockerFixture(config, config.output / "native-0", "qa-only")
    harness.prepare(config.participants[0])
    calls = []

    def command(*args, **kwargs):
        calls.append(args)
        return "logs"

    def fail(*args):
        raise OSError("isolated full disk")

    monkeypatch.setattr(harness, "command", command)
    monkeypatch.setattr(harness, "diagnostics", fail)
    harness.started = True
    harness.close()
    assert calls[-1][0] == "down"


def experiment(tmp_path):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    (fixture / "database.sql").write_text(
        "-- isolated fixture, never a production restore\n"
    )
    character = {
        "id": 7,
        "level": 8,
        "experience": 4200,
        "posx": 100,
        "posy": 100,
        "posz": 7,
    }
    (fixture / "character.json").write_text(json.dumps(character))
    world = tmp_path / "fixture-map.otbm"
    world.write_bytes(b"offline fixture only")
    return Experiment(
        name="qa",
        output=tmp_path / "runs",
        fixture=fixture,
        world_map=world,
        budget_file=tmp_path / "shared-budget.db",
        bot_id=7,
        participants=[Participant(name="native", kind="native")],
        source_revision="test",
        expected_initial_sha256=fixture_hash(fixture, world),
        repetitions=1,
        seconds=10,
    )


def test_preflight_detects_changed_initial_conditions_and_has_no_game_side_effects(
    tmp_path,
):
    config = experiment(tmp_path)
    assert preflight(config)["runs"] == 1
    assert not config.output.exists()
    (config.fixture / "database.sql").write_text("changed initial state")
    with pytest.raises(ValueError, match="hash"):
        preflight(config)


async def test_live_execution_is_explicit_and_failed_attempts_are_preserved(
    tmp_path, monkeypatch
):
    config = experiment(tmp_path)
    with pytest.raises(ValueError, match="live"):
        await run_campaign(config)
    starts = []

    class Harness(DockerFixture):
        def start_database(self):
            starts.append("database")

        def character(self):
            return {
                "id": 7,
                "level": 8,
                "experience": 4200,
                "posx": 100,
                "posy": 100,
                "posz": 7,
            }

        def start_game(self):
            raise RuntimeError("fixture failure")

        def close(self):
            starts.append("closed")

    monkeypatch.setattr("canary_brain.benchmark.DockerFixture", Harness)
    with pytest.raises(RuntimeError, match="fixture failure"):
        await run_campaign(config, live=True)
    reader = ReplayReader(config.output / "recording.sqlite3")
    assert reader.run("qa:native:0")["status"] == "failed"
    assert starts == ["database", "closed"]
    result = await run_campaign(config, live=True)
    assert result["participants"][0]["statuses"] == ["failed"]
    assert starts == ["database", "closed", "closed"]


def test_isolated_compose_has_no_production_ports_or_named_volumes(tmp_path):
    config = experiment(tmp_path)
    harness = DockerFixture(config, config.output / "native-0", "qa-only")
    harness.directory.parent.mkdir()
    harness.prepare(config.participants[0])
    compose = json.loads(harness.compose.read_text())
    assert harness.project.startswith("canary-bench-")
    assert "volumes" not in compose
    assert all("ports" not in service for service in compose["services"].values())
    native = json.loads((harness.directory / "config/server.json").read_text())
    assert native["mode"] == "shadow" and native["keep_awake"] is True


def test_synthetic_demo_is_labeled_and_portable_report_is_offline(tmp_path):
    path = tmp_path / "recording.db"
    runs = demo(path)
    reader = ReplayReader(path)
    result = campaign(reader, runs)
    assert all(r["manifest"]["synthetic"] for r in result["runs"])
    assert result["verdict"] == "descriptive_only"
    report = tmp_path / "report.html"
    export_report(reader, runs, report)
    html = report.read_text()
    assert "window.REPLAY_ARCHIVE=" in html
    assert 'src="/replay.js"' not in html
    assert 'href="/replay.css"' not in html


async def test_decision_fixtures_never_fabricate_counterfactual_game_results():
    rows = await evaluate_decisions(
        FakeProvider(), [{"observation": observation(), "expected": "continue"}]
    )
    assert rows[0]["matches_expected"] is True
    assert "xp" not in rows[0] and "survival" not in rows[0]


@pytest.mark.parametrize(
    "change",
    [
        lambda c: c["router_settings"].update(num_retries=1),
        lambda c: c["router_settings"].update(fallbacks=[{"a": ["b"]}]),
        lambda c: c["model_list"].append(c["model_list"][0]),
        lambda c: c["model_list"][0]["litellm_params"].update(order=2),
        lambda c: c["litellm_settings"].update(cache=True),
        lambda c: c["litellm_settings"].update(drop_params=True),
    ],
)
def test_gateway_policy_rejects_hidden_changes_to_benchmark_conditions(change):
    config = {
        "router_settings": {"num_retries": 0},
        "litellm_settings": {"num_retries": 0, "drop_params": False},
        "model_list": [
            {
                "model_name": "a",
                "litellm_params": {"model": "test/model"},
                "model_info": {"id": "a"},
            }
        ],
    }
    assert validate_policy(config) == {"a"}
    change(config)
    with pytest.raises(ValueError):
        validate_policy(config)


def attempt(config, participant="native"):
    return Manifest(
        run_id=f"{config.name}:{participant}:0",
        bot_id=config.bot_id,
        lineage=f"{config.name}:0",
        experiment=config.name,
        participant=participant,
        initial_sha256=config.expected_initial_sha256,
        configuration_sha256=digest(config.model_dump(mode="json")),
    )


def test_resume_monthly_budget_only_reserves_attempts_not_already_recorded(tmp_path):
    config = experiment(tmp_path)
    credential = tmp_path / "private.env"
    credential.write_text("LITELLM_API_KEY=qa-only\n")
    credential.chmod(0o600)
    config = config.model_copy(
        update={
            "participants": [
                Participant(name="model", kind="litellm", gateway=gateway())
            ],
            "repetitions": 2,
            "run_cap_nanousd": 2 * USD,
            "campaign_cap_nanousd": 4 * USD,
            "gateway_credential": credential,
            "game_image": "sha256:" + "a" * 64,
            "database_image": "mariadb@sha256:" + "b" * 64,
        }
    )
    budget = Store(config.budget_file)
    budget.reserve("spent", 47 * USD, month_now())
    budget.settle("spent", 47 * USD)
    recording = RecordingStore(config.output / "recording.sqlite3")
    recording.begin(attempt(config, "model"))
    recording.finish("qa:model:0", "completed")
    result = preflight(config)
    assert result["worst_case_nanousd"] == 4 * USD
    assert result["remaining_nanousd"] == 2 * USD


async def test_resume_cleans_the_same_project_before_closing_an_interrupted_attempt(
    tmp_path, monkeypatch
):
    config = experiment(tmp_path)
    recording = RecordingStore(config.output / "recording.sqlite3")
    recording.begin(attempt(config))
    harness = DockerFixture(config, config.output / "native-0", "unused")
    harness.prepare(config.participants[0])
    closed = []

    def close(self):
        assert self.started
        assert ReplayReader(recording.path).run("qa:native:0")["status"] == "running"
        closed.append(self.project)

    monkeypatch.setattr(DockerFixture, "close", close)
    await run_campaign(config, live=True)
    assert len(closed) == 1
    assert ReplayReader(recording.path).run("qa:native:0")["status"] == "interrupted"


async def test_failed_orphan_cleanup_keeps_attempt_pending_for_next_resume(
    tmp_path, monkeypatch
):
    config = experiment(tmp_path)
    recording = RecordingStore(config.output / "recording.sqlite3")
    recording.begin(attempt(config))
    DockerFixture(config, config.output / "native-0", "unused").prepare(
        config.participants[0]
    )

    def fail(self):
        raise RuntimeError("cleanup unavailable")

    monkeypatch.setattr(DockerFixture, "close", fail)
    with pytest.raises(RuntimeError, match="cleanup unavailable"):
        await run_campaign(config, live=True)
    assert ReplayReader(recording.path).run("qa:native:0")["status"] == "running"


async def test_running_orchestrator_cannot_be_mistaken_for_an_orphan(tmp_path):
    config = experiment(tmp_path)
    with campaign_lease(config.output), pytest.raises(ValueError, match="orchestrator"):
        await run_campaign(config, live=True)
