"""Exercise the live adapters' preparation without starting a campaign."""

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from canary_brain import benchmark


@pytest.mark.parametrize(
    "filename", ["m5_current_qualification.py", "m5_runner_smoke.py"]
)
def test_internal_network_keeps_its_owner(tmp_path, monkeypatch, filename):
    def reject_subprocess(*args, **kwargs):
        pytest.fail("preparation and stubbed ownership checks must stay offline")

    monkeypatch.setattr(benchmark.subprocess, "run", reject_subprocess)
    source = Path(__file__).with_name(filename)
    adapter = next(
        node
        for node in ast.walk(ast.parse(source.read_text()))
        if isinstance(node, ast.ClassDef) and node.name == "AttestedFixture"
    )
    # The qualification class closes over active_fixture. Neither entry point runs here.
    factory = ast.parse(
        "def build():\n    active_fixture = None\n    return AttestedFixture\n"
    )
    factory.body[0].body.insert(1, adapter)
    namespace = {
        "base": benchmark.DockerFixture,
        "original": benchmark.DockerFixture,
        "json": json,
        "database": "fixture-database",
        "args": None,
        "frozen": {"guid": 1},
        "apply_short_trace_guid": lambda *_: None,
    }
    exec(compile(factory, str(source), "exec"), namespace)  # noqa: S102 - checked-in adapter

    seed = tmp_path / "fixture"
    seed.mkdir()
    (seed / "database.sql").touch()
    experiment = SimpleNamespace(
        output=tmp_path / "runs",
        fixture=seed,
        world_map=tmp_path / "world.otbm",
        bot_id=1,
        game_image="fixture-game",
        database_image="fixture-database",
    )
    fixture = namespace["build"]()(
        experiment, experiment.output / "native-0", "qa:native:0"
    )
    fixture.prepare(benchmark.Participant(name="native", kind="native"))

    network = json.loads(fixture.compose.read_text())["networks"]["default"]
    assert network["internal"] is True
    assert (
        network["labels"][benchmark.BENCHMARK_OWNER_LABEL]
        == fixture.read_ownership()["owner_id"]
    )
    monkeypatch.setattr(fixture, "docker_metadata", lambda *args: "")
    fixture.validate_docker_ownership()
