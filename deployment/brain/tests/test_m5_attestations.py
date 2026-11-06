"""Actual Docker metadata is simulated; no daemon, provider or ledger is used."""

import asyncio
import hashlib
import json
import stat
import subprocess
from types import SimpleNamespace

import pytest
from tools import m5_pilot as pilot


class Docker:
    def __init__(self):
        self.containers = {}
        self.networks = {}
        self.calls = []
        self.owner = None
        self.failure = None
        self.leftover = None
        self.before_start = None
        self.image_ids = {}

    def container(self, fixture, service, state):
        compose = json.loads(fixture.compose.read_text())
        network = fixture.project + "_default"
        mounts = []
        for binding in compose["services"][service]["volumes"]:
            parts = binding.split(":")
            mounts.append(
                {
                    "Type": "bind",
                    "Source": parts[0],
                    "Destination": parts[1],
                    "RW": len(parts) == 2 or parts[2] != "ro",
                }
            )
        return {
            "id": ("a" if service == "database" else "b") * 64,
            "project": fixture.project,
            "service": service,
            "oneoff": "False",
            "image": self.image_ids.get(
                getattr(fixture.experiment, service + "_image"),
                getattr(fixture.experiment, service + "_image"),
            ),
            "state": state,
            "network_mode": network,
            "networks": {network: {"NetworkID": "c" * 64}},
            "mounts": mounts,
            "ports": {"7171/tcp": None},
            "port_bindings": {},
            "Config": {"Env": ["OPENAI_API_KEY=never-export-this"]},
            "AuthHeader": "Bearer never-export-this",
        }

    def command(self, fixture, *arguments, **kwargs):
        self.calls.append(("compose", arguments, kwargs))
        self.owner = fixture
        if arguments[0] == "up":
            row = self.container(fixture, "database", "running")
            self.containers[row["id"]] = row
            self.networks["c" * 64] = {
                "id": "c" * 64,
                "project": fixture.project,
                "name": fixture.project + "_default",
                "internal": True,
                "scope": "local",
                "driver": "bridge",
                "containers": {row["id"]: {}},
                "Config": {"Env": ["DO_NOT_EXPORT=this-either"]},
            }
        elif arguments[0] == "create":
            row = self.container(fixture, "game", "created")
            self.containers[row["id"]] = row
        elif arguments[0] == "start":
            record = json.loads(
                (fixture.directory / "trial-attestation.json").read_text()
            )
            assert record["images_verified"] is True
            if self.before_start:
                self.before_start()
            self.containers["b" * 64]["state"] = "running"
            self.networks["c" * 64]["containers"]["b" * 64] = {}
        elif arguments[0] == "down":
            if self.failure:
                raise self.failure
            self.containers.clear()
            self.networks.clear()
            if self.leftover:
                self.containers[self.leftover["id"]] = self.leftover
        return ""

    def query(self, arguments, **kwargs):
        self.calls.append(("docker", arguments, kwargs))
        assert kwargs == {"text": True, "cwd": "/", "timeout": 20}
        assert arguments[0] == "docker"
        kind, operation = arguments[1:3]
        if kind == "image":
            assert operation == "inspect"
            assert arguments[3:5] == ["--format", "{{.Id}}"]
            return self.image_ids[arguments[-1]]
        rows = self.containers if kind == "container" else self.networks
        if operation == "ls":
            assert (
                arguments[-1]
                == "label=com.docker.compose.project=" + self.owner.project
            )
            return "\n".join(rows)
        assert operation == "inspect"
        assert arguments[3] == "--format"
        assert ".Config.Env" not in arguments[4] and "AuthHeader" not in arguments[4]
        return json.dumps(rows[arguments[-1]])


@pytest.fixture
def setup(tmp_path, monkeypatch):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    (fixture / "database.sql").write_text("-- isolated fake fixture\n")
    world = tmp_path / "world.otbm"
    world.write_text("fake world")
    output = tmp_path / "game"
    output.mkdir()
    experiment = pilot.benchmark.Experiment(
        name="attest-pilot",
        output=output,
        fixture=fixture,
        world_map=world,
        budget_file=tmp_path / "must-not-open-ledger.sqlite3",
        bot_id=65001,
        participants=[{"name": "native", "kind": "native"}],
        repetitions=1,
        game_image="sha256:" + "1" * 64,
        database_image="sha256:" + "2" * 64,
        source_revision="a" * 40,
        expected_initial_sha256="b" * 64,
    )
    engine = Docker()
    monkeypatch.setattr(pilot.subprocess, "check_output", engine.query)
    # This closure keeps the mocked method's fixture instance as an argument.
    monkeypatch.setattr(
        pilot.benchmark.DockerFixture,
        "command",
        lambda own, *args, **kwargs: engine.command(own, *args, **kwargs),
    )
    monkeypatch.setattr(
        pilot.runtime, "read_credential", lambda *a: pytest.fail("no credentials")
    )
    return experiment, engine


async def run_trial(monkeypatch, experiment, action):
    async def campaign(config, live):
        assert live
        identity = f"{config.name}:native:0"
        trial = pilot.benchmark.DockerFixture(
            config,
            config.output / "native-0",
            hashlib.sha256(identity.encode()).hexdigest(),
        )
        trial.prepare(config.participants[0])
        trial.start_database()
        try:
            return await action(trial)
        finally:
            trial.close()

    monkeypatch.setattr(pilot.benchmark, "run_campaign", campaign)
    return await pilot.run_attested_campaign(experiment)


def record(experiment):
    return json.loads((experiment.output / "trial-attestations.json").read_text())[
        "trials"
    ]["attest-pilot:native:0"]


async def test_real_metadata_precedes_game_start_and_reporter_gets_private_scoped_map(
    setup, monkeypatch
):
    experiment, engine = setup

    async def action(trial):
        trial.start_game()

    await run_trial(monkeypatch, experiment, action)
    result = record(experiment)
    assert result["game_image"] == experiment.game_image
    assert result["database_image"] == experiment.database_image
    assert result["images_verified"] and result["resources_cleaned"]
    assert result["verified_before_game_start"] and result["remaining_containers"] == []
    for path in [
        experiment.output / "trial-attestations.json",
        experiment.output / "native-0/trial-attestation.json",
    ]:
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        text = path.read_text()
        assert (
            "never-export-this" not in text
            and "AuthHeader" not in text
            and '"Env"' not in text
        )
    assert (
        len(
            [
                call
                for call in engine.calls
                if call[0] == "compose" and call[1][0] == "down"
            ]
        )
        == 1
    )
    assert not experiment.budget_file.exists()
    from tools import m5_report

    rows = m5_report.trials_from_root(
        experiment.output,
        {"plan": experiment.model_dump(mode="json"), "preflight": {"character": {}}},
        json.loads((experiment.output / "trial-attestations.json").read_text()),
    )
    assert len(rows) == 1
    assert rows[0]["images_verified"] is True and rows[0]["resources_cleaned"] is True
    assert rows[0]["game_image"] == experiment.game_image


async def test_manifest_digest_resolves_to_container_config_id_before_start(
    setup, monkeypatch
):
    experiment, engine = setup
    experiment.game_image = "registry.example/game@sha256:" + "3" * 64
    experiment.database_image = "registry.example/database@sha256:" + "4" * 64
    engine.image_ids = {
        experiment.game_image: "sha256:" + "1" * 64,
        experiment.database_image: "sha256:" + "2" * 64,
    }

    async def action(trial):
        trial.start_game()

    await run_trial(monkeypatch, experiment, action)
    result = record(experiment)
    assert result["images_verified"] is True
    assert result["game_image"] == experiment.game_image
    assert result["database_image"] == experiment.database_image
    assert {row["image"] for row in result["containers"]} == set(
        engine.image_ids.values()
    )
    assert (
        len(
            [
                call
                for call in engine.calls
                if call[0] == "docker" and call[1][1] == "image"
            ]
        )
        == 4
    )
    from tools import m5_report

    rows = m5_report.trials_from_root(
        experiment.output,
        {"plan": experiment.model_dump(mode="json"), "preflight": {"character": {}}},
        json.loads((experiment.output / "trial-attestations.json").read_text()),
    )
    assert rows[0]["game_image"] == experiment.game_image


async def test_manifest_digest_with_different_container_content_stops_before_start(
    setup, monkeypatch
):
    experiment, engine = setup
    experiment.game_image = "registry.example/game@sha256:" + "3" * 64
    engine.image_ids[experiment.game_image] = "sha256:" + "1" * 64
    command = engine.command

    def wrong_content(trial, *args, **kwargs):
        value = command(trial, *args, **kwargs)
        if args[0] == "create":
            engine.containers["b" * 64]["image"] = "sha256:" + "9" * 64
        return value

    engine.command = wrong_content

    async def action(trial):
        trial.start_game()

    with pytest.raises(ValueError, match="image differs"):
        await run_trial(monkeypatch, experiment, action)
    assert record(experiment)["images_verified"] is False
    assert not any(
        call[0] == "compose" and call[1][0] == "start" for call in engine.calls
    )


async def test_prepare_fails_before_attempt_directory_and_keeps_aggregate_evidence(
    setup, monkeypatch
):
    experiment, engine = setup
    original_prepare = pilot.benchmark.DockerFixture.prepare

    def fail_prepare(self, participant):
        raise OSError("private prepare failure")

    monkeypatch.setattr(pilot.benchmark.DockerFixture, "prepare", fail_prepare)

    async def campaign(config, live):
        identity = f"{config.name}:native:0"
        trial = pilot.benchmark.DockerFixture(
            config,
            config.output / "native-0",
            hashlib.sha256(identity.encode()).hexdigest(),
        )
        engine.owner = trial
        try:
            trial.prepare(config.participants[0])
        finally:
            trial.close()

    monkeypatch.setattr(pilot.benchmark, "run_campaign", campaign)
    try:
        with pytest.raises(OSError, match="private prepare failure"):
            await pilot.run_attested_campaign(experiment)
    finally:
        monkeypatch.setattr(pilot.benchmark.DockerFixture, "prepare", original_prepare)
    assert not (experiment.output / "native-0").exists()
    result = record(experiment)
    assert result["resources_cleaned"] is True
    assert result["remaining_containers"] == []
    assert result["remaining_networks"] == []


@pytest.mark.parametrize(
    "problem",
    [
        "image",
        "project",
        "ports",
        "mount",
        "network",
        "database_network",
        "database_endpoint",
        "declared_foreign_mount",
    ],
)
async def test_unproven_identity_scope_or_mount_stops_before_game_and_api(
    setup, monkeypatch, problem
):
    experiment, engine = setup
    command = engine.command

    def change(trial, *args, **kwargs):
        result = command(trial, *args, **kwargs)
        if args[0] == "create":
            row = engine.containers["b" * 64]
            if problem == "image":
                row["image"] = "sha256:" + "9" * 64
            elif problem == "project":
                row["project"] = "production"
            elif problem == "ports":
                row["port_bindings"] = {"7171/tcp": [{"HostPort": "7171"}]}
            elif problem == "mount":
                row["mounts"][0]["Source"] = "/production/data"
            elif problem == "declared_foreign_mount":
                row["mounts"][0]["Source"] = "/production/data"
                compose = json.loads(trial.compose.read_text())
                compose["services"]["game"]["volumes"][0] = (
                    "/production/data:/etc/canary-brain:ro"
                )
                trial.compose.write_text(json.dumps(compose))
            elif problem == "database_network":
                engine.containers["a" * 64]["networks"][trial.project + "_default"][
                    "NetworkID"
                ] = "d" * 64
            elif problem == "database_endpoint":
                engine.networks["c" * 64]["containers"].clear()
            else:
                engine.networks["c" * 64]["internal"] = False
        return result

    engine.command = change

    async def action(trial):
        trial.start_game()
        pytest.fail("unqualified game must not run")

    with pytest.raises(ValueError):
        await run_trial(monkeypatch, experiment, action)
    result = record(experiment)
    assert result["images_verified"] is False and result["resources_cleaned"] is True
    assert result["failures"][0]["phase"] == "pre_start_images"
    assert not any(
        call[0] == "compose" and call[1][0] == "start" for call in engine.calls
    )


@pytest.mark.parametrize("foreign", [False, True])
async def test_active_or_foreign_leftover_never_counts_as_clean_or_gets_deleted_again(
    setup, monkeypatch, foreign
):
    experiment, engine = setup

    async def action(trial):
        trial.start_game()
        engine.leftover = engine.container(trial, "game", "running")
        if foreign:
            engine.leftover["project"] = "unrelated-project"

    with pytest.raises(RuntimeError, match="cleanup could not be verified"):
        await run_trial(monkeypatch, experiment, action)
    result = record(experiment)
    assert result["images_verified"] is True and result["resources_cleaned"] is False
    assert result["remaining_containers"][0]["state"] == "running"
    assert (
        len(
            [
                call
                for call in engine.calls
                if call[0] == "compose" and call[1][0] == "down"
            ]
        )
        == 1
    )
    assert engine.containers


async def test_close_failure_is_preserved_and_never_attested_as_clean(
    setup, monkeypatch
):
    experiment, engine = setup
    engine.failure = OSError("simulated private close failure")

    async def action(trial):
        trial.start_game()

    with pytest.raises(OSError, match="simulated private close failure"):
        await run_trial(monkeypatch, experiment, action)
    result = record(experiment)
    assert result["resources_cleaned"] is False
    assert {row["phase"] for row in result["failures"]} == {
        "canonical_close",
        "cleanup_verification",
    }
    assert "simulated private close failure" not in json.dumps(result)


async def test_observer_and_attestation_failures_both_remain_evidence(
    setup, monkeypatch
):
    experiment, engine = setup

    async def worker(_, stopped):
        await stopped.wait()

    async def observer(*args):
        raise ValueError("private observer diagnostic")

    monkeypatch.setattr(pilot.runtime, "run", worker)
    monkeypatch.setattr(pilot, "observe_status", observer)

    async def action(trial):
        trial.start_game()
        engine.leftover = engine.container(trial, "game", "running")
        await pilot.benchmark.run(
            SimpleNamespace(state_file=trial.directory / "worker.sqlite3"),
            asyncio.Event(),
        )

    with pytest.raises(RuntimeError, match="cleanup could not be verified"):
        await run_trial(monkeypatch, experiment, action)
    result = record(experiment)
    assert {row["phase"] for row in result["failures"]} >= {
        "observer",
        "cleanup_verification",
    }
    assert json.loads(
        (experiment.output / "native-0/status-observer-error.json").read_text()
    ) == {"error_type": "ValueError"}
    assert "private observer diagnostic" not in json.dumps(result)


async def test_cleanup_query_timeout_is_false_and_propagates(setup, monkeypatch):
    experiment, engine = setup
    query = engine.query

    def fail_after_down(arguments, **kwargs):
        if any(row[0] == "compose" and row[1][0] == "down" for row in engine.calls):
            raise subprocess.TimeoutExpired(arguments, 20)
        return query(arguments, **kwargs)

    monkeypatch.setattr(pilot.subprocess, "check_output", fail_after_down)

    async def action(trial):
        trial.start_game()

    with pytest.raises(subprocess.TimeoutExpired):
        await run_trial(monkeypatch, experiment, action)
    result = record(experiment)
    assert result["resources_cleaned"] is False
    assert result["failures"][-1] == {
        "phase": "cleanup_verification",
        "error_type": "TimeoutExpired",
    }


async def test_different_container_after_start_invalidates_images(setup, monkeypatch):
    experiment, engine = setup
    command = engine.command

    def replace_after_start(trial, *args, **kwargs):
        value = command(trial, *args, **kwargs)
        if args[0] == "start":
            game = engine.containers.pop("b" * 64)
            game["id"] = "d" * 64
            engine.containers[game["id"]] = game
            engine.networks["c" * 64]["containers"].pop("b" * 64)
            engine.networks["c" * 64]["containers"][game["id"]] = {}
        return value

    engine.command = replace_after_start

    async def action(trial):
        trial.start_game()

    with pytest.raises(ValueError, match="changed after"):
        await run_trial(monkeypatch, experiment, action)
    assert record(experiment)["images_verified"] is False


async def test_remaining_project_network_prevents_cleanup_claim(setup, monkeypatch):
    experiment, engine = setup
    command = engine.command

    def retain_network(trial, *args, **kwargs):
        before = dict(engine.networks)
        value = command(trial, *args, **kwargs)
        if args[0] == "down":
            engine.networks.update(before)
        return value

    engine.command = retain_network

    async def action(trial):
        trial.start_game()

    with pytest.raises(RuntimeError, match="cleanup could not be verified"):
        await run_trial(monkeypatch, experiment, action)
    result = record(experiment)
    assert result["resources_cleaned"] is False
    assert len(result["remaining_networks"]) == 1
    assert result["remaining_containers"] == []
