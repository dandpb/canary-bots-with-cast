"""A skipped decision is observable without becoming a billable request."""

from types import SimpleNamespace

import pytest
from test_protocol import observation

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.provider import Prices, ProviderBackoff
from canary_brain.recording import (
    Manifest,
    Recorder,
    RecordingConfiguration,
    ReplayReader,
    attribution,
)
from canary_brain.store import Store


async def test_backoff_emits_attributed_deadline_without_reserve_or_transmission(
    tmp_path,
):
    calls = []

    async def create(**body):
        calls.append(body)
        raise TimeoutError("synthetic transport timeout")

    store = Store(tmp_path / "ledger.sqlite3", cap=100_000)
    path = tmp_path / "replay.sqlite3"
    manifest = Manifest(run_id="backoff-observability", bot_id=7, lineage="fixture")
    recorder = Recorder(RecordingConfiguration(path=path, namespace="test"), [manifest])
    gateway = GatewayConfiguration(
        alias="alias-a",
        effective_model="model-a",
        deployment_id="deployment-a",
        provider="test",
        version="offline",
        configuration_sha256="a" * 64,
        prices=Prices(
            version="offline",
            input_nanousd=1,
            cached_nanousd=1,
            cache_write_nanousd=1,
            output_nanousd=2,
        ),
    )
    provider = GatewayProvider(
        store,
        SimpleNamespace(
            responses=SimpleNamespace(with_raw_response=SimpleNamespace(create=create))
        ),
        gateway=gateway,
        recorder=recorder,
    )
    try:
        with attribution(7, "transmitted-decision"), pytest.raises(TimeoutError):
            await provider.decide(Observation.model_validate(observation()))
        before_skip = store.budget()
        with (
            attribution(7, "skipped-decision"),
            pytest.raises(ProviderBackoff) as skipped,
        ):
            await provider.decide(Observation.model_validate(observation()))
        assert isinstance(skipped.value, RuntimeError)
        assert len(calls) == 1
        assert store.budget() == before_skip
        assert len(store.records("request")) == 1
        with store.connection() as db:
            assert db.execute("SELECT COUNT(*) FROM requests").fetchone()[0] == 1
        recorder.flush()
        events = list(ReplayReader(path).all_events(manifest.run_id))
        requests = [event["data"] for event in events if event["kind"] == "request"]
        assert sum(row["phase"] == "reserved" for row in requests) == 1
        assert sum(row["phase"] == "failed" for row in requests) == 1
        skip = next(row for row in requests if row["phase"] == "skipped")
        assert skip["reason"] == "backoff"
        assert skip["decision_id"] == "skipped-decision"
        assert skip["requested_model"] == "alias-a"
        assert skip["endpoint"] == "responses"
        assert skip["deadline_ms"] == 1200
        assert skip["reserved_nanousd"] == 0
        with store.connection() as db:
            assert (
                db.execute(
                    "SELECT COUNT(*) FROM requests WHERE id=?", (skip["request_id"],)
                ).fetchone()[0]
                == 0
            )
    finally:
        recorder.close()
