"""Unknown cache-write prices retain liability rather than claiming free writes."""

from types import SimpleNamespace

import pytest
from test_protocol import observation

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.provider import Prices
from canary_brain.store import Store


def participant(store, write_price, written):
    calls = []

    async def create(**body):
        calls.append(body)
        response = {
            "id": "synthetic-upstream-request",
            "model": "model-a",
            "usage": {
                "input_tokens": 20,
                "input_tokens_details": {
                    "cached_tokens": 0,
                    "cache_write_tokens": written,
                },
                "output_tokens": 2,
            },
            "output": [
                {
                    "type": "function_call",
                    "name": "choose_action",
                    "arguments": '{"candidate_id":"resupply"}',
                }
            ],
        }
        return SimpleNamespace(
            headers={"x-litellm-model-id": "deployment-a"},
            parse=lambda: SimpleNamespace(model_dump=lambda **_: response),
        )

    gateway = GatewayConfiguration(
        alias="alias-a",
        effective_model="model-a",
        deployment_id="deployment-a",
        provider="gemini" if write_price is None else "test",
        version="offline-fixture",
        configuration_sha256="a" * 64,
        prices=Prices(
            version="explicit-unknown-writes"
            if write_price is None
            else "known-writes",
            input_nanousd=1,
            cached_nanousd=1,
            cache_write_nanousd=write_price,
            output_nanousd=2,
        ),
    )
    client = SimpleNamespace(
        responses=SimpleNamespace(with_raw_response=SimpleNamespace(create=create))
    )
    return GatewayProvider(store, client, gateway=gateway), calls


async def test_unknown_cache_write_price_retains_full_reservation_after_restart(
    tmp_path,
):
    path = tmp_path / "shared-ledger.sqlite3"
    store = Store(path, cap=100_000)
    provider, calls = participant(store, None, 5)
    with pytest.raises(ValueError, match="cache.write.*price"):
        await provider.decide(Observation.model_validate(observation()))
    assert len(calls) == 1
    before_restart = store.budget()
    assert before_restart["spent"] == 0
    assert before_restart["reserved"] > 0
    assert before_restart["available"] < before_restart["cap"]
    reopened = Store(path, cap=100_000)
    assert reopened.budget() == before_restart
    request = reopened.records("request")[0][1]
    assert request["error"] == "UnpricedCacheWrite"
    assert request["unsettled"] is True


@pytest.mark.parametrize(
    "write_price,written,expected_spent",
    [(None, 0, 24), (0, 5, 19), (3, 5, 34)],
)
async def test_no_writes_unknown_price_and_known_free_or_paid_writes_settle_normally(
    tmp_path, write_price, written, expected_spent
):
    store = Store(tmp_path / "ledger.sqlite3", cap=100_000)
    provider, calls = participant(store, write_price, written)
    assert (
        await provider.decide(Observation.model_validate(observation())) == "resupply"
    )
    assert len(calls) == 1
    assert store.budget()["spent"] == expected_spent
    assert store.budget()["reserved"] == 0
