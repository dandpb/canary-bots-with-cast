import json

import pytest
from canary_brain.benchmark import (
    DockerFixture,
    Experiment,
    Participant,
    demo,
    evaluate_decisions,
    fixture_hash,
    preflight,
    run_campaign,
)
from canary_brain.gateway_policy import validate_policy
from canary_brain.recording import ReplayReader
from canary_brain.replay import campaign, export_report
from canary_brain.testing import FakeProvider
from test_protocol import observation


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
    assert starts == ["database", "closed"]


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
