"""Replay versioned QA evidence without starting a game or calling a model."""

import json
from pathlib import Path

import pytest
from test_benchmark import attempt, experiment
from test_gateway import gateway

from canary_brain import benchmark
from canary_brain.gateway import GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.provider import Provider
from canary_brain.recording import RecordingStore, ReplayReader
from canary_brain.replay import import_archive
from canary_brain.store import Store

EVIDENCE = Path(__file__).resolve().parents[1] / "evidence/2026-11-06"
QUALIFIED = "m5-final-free-qualified"
INTERRUPTED = "m5-final-interrupted-attempts"
PARTIAL = "m5-none-v3-partial-c2c3972c"


@pytest.mark.parametrize(
    ("archive", "status", "sample_span_ms"),
    [
        (f"{QUALIFIED}/native/native.replay.zip", "completed", 1800387),
        (f"{QUALIFIED}/fake/fake.replay.zip", "completed", 1801000),
        (f"{INTERRUPTED}/native/native.replay.zip", "interrupted", 1338798),
        (f"{INTERRUPTED}/fake/fake.replay.zip", "interrupted", 1338790),
        (f"{PARTIAL}/replays/native-partial.replay.zip", "failed", 220803),
    ],
)
async def test_m5_resume_preserves_historical_attempt(
    tmp_path, monkeypatch, archive, status, sample_span_ms
):
    original = tmp_path / "archive.sqlite3"
    archived_id = import_archive(EVIDENCE / archive, original)
    reader = ReplayReader(original)
    metadata = reader.run(archived_id)
    events = list(reader.all_events(archived_id))
    samples = [event["t_ms"] for event in events if event["kind"] == "sample"]
    assert max(samples) - min(samples) == sample_span_ms
    assert metadata["status"] == status

    config = experiment(tmp_path)
    manifest = attempt(config)
    output = config.output / "recording.sqlite3"
    store = RecordingStore(output)
    store.import_run(manifest, metadata, events)
    recoveries = []

    class Fixture(benchmark.DockerFixture):
        def recover(self, *, ownership_expected=False):
            recoveries.append(self.directory)

        def prepare(self, participant):
            pytest.fail("a historical attempt must not be executed again")

    monkeypatch.setattr(benchmark, "DockerFixture", Fixture)
    result = await benchmark.run_campaign(config, live=True)

    assert recoveries == [config.output / "native-0"]
    retained = ReplayReader(output).run(manifest.run_id)
    assert result["participants"][0]["statuses"] == [status]
    for field in ("status", "event_count", "duration_ms", "incomplete"):
        assert retained[field] == metadata[field]

    # A fresh retry can retain this evidence only with a separate identity.
    if status == "interrupted":
        with pytest.raises(ValueError, match="closed"):
            store.begin(manifest)
        retry = manifest.model_copy(update={"run_id": f"{manifest.run_id}:retry"})
        assert store.begin(retry) == (0, None)
        assert ReplayReader(output).run(manifest.run_id)["status"] == "interrupted"


@pytest.mark.parametrize(
    ("archive", "expected"),
    [
        (f"{QUALIFIED}/fake/fake.replay.zip", 606),
        (f"{INTERRUPTED}/fake/fake.replay.zip", 447),
        ("m5-navigation-diagnostics/E/e.replay.zip", 14),
    ],
)
async def test_decision_adapters_agree_on_historical_offers(
    tmp_path, monkeypatch, archive, expected
):
    original = tmp_path / "archive.sqlite3"
    run_id = import_archive(EVIDENCE / archive, original)
    decisions = [
        event["data"]
        for event in ReplayReader(original).all_events(run_id)
        if event["kind"] == "decision"
    ]
    proposed = {
        row["decision_id"]: row["candidate"]
        for row in decisions
        if row["phase"] == "model_proposed"
    }
    requested = [row for row in decisions if row["phase"] == "requested"]
    assert len(requested) == expected
    providers = {
        "decisions": Provider(Store(tmp_path / "direct.sqlite3"), None, 2.5),
        "responses": GatewayProvider(
            Store(tmp_path / "gateway.sqlite3"), None, 2.5, gateway=gateway()
        ),
    }
    calls = []
    replayed_choice = ""

    async def respond(endpoint, body, timeout, *, fast=False, tactical=False):
        calls.append((endpoint, timeout, tactical))
        if endpoint == "decisions":
            return {
                "answers": [
                    {"name": "action", "type": "choice", "choice": replayed_choice}
                ]
            }
        return {
            "output": [
                {
                    "type": "function_call",
                    "name": "choose_action",
                    "arguments": json.dumps({"candidate_id": replayed_choice}),
                }
            ]
        }

    for provider in providers.values():
        monkeypatch.setattr(provider, "_request", respond)

    for request in requested:
        # The replay intentionally omits the lease. It is irrelevant to model choice.
        observation = Observation.model_validate(
            {**request["observation"], "lease": "historical-replay"}
        )
        replayed_choice = proposed[request["decision_id"]]
        offered = observation.actions
        for endpoint, provider in providers.items():
            calls.clear()
            assert (
                await provider.decide(observation, request["memory"]) == replayed_choice
            )
            if len(offered) == 1:
                assert calls == []
            else:
                actions = {item.action for item in offered}
                tactical = bool(actions & {"target", "retreat"}) and actions <= {
                    "target",
                    "retreat",
                    "continue",
                    "hold",
                }
                assert calls == [
                    (
                        endpoint,
                        min(2.5, min(a.ttl_ms for a in offered) / 1000),
                        tactical,
                    )
                ]

    multi_offer = next(
        row for row in requested if len(row["observation"]["actions"]) > 1
    )
    observation = Observation.model_validate(
        {**multi_offer["observation"], "lease": "historical-replay"}
    )
    replayed_choice = "not-offered-in-this-observation"
    for provider in providers.values():
        with pytest.raises(ValueError, match="unavailable candidate"):
            await provider.decide(observation, multi_offer["memory"])
