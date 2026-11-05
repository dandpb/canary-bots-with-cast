import json
from types import SimpleNamespace

import pytest
from test_protocol import observation

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.provider import Prices
from canary_brain.store import BudgetExceeded, Store


def gateway():
    return GatewayConfiguration(
        alias="participant-a",
        effective_model="model-a",
        deployment_id="deployment-a",
        provider="test",
        version="pinned-test",
        configuration_sha256="a" * 64,
        prices=Prices(
            version="test",
            input_nanousd=1,
            cached_nanousd=1,
            cache_write_nanousd=1,
            output_nanousd=2,
        ),
    )


def client(model="model-a", deployment="deployment-a"):
    calls = []

    class Raw:
        def __init__(self):
            self.headers = {
                "x-litellm-model-id": deployment,
                "x-litellm-call-id": "gateway-request",
            }

        def parse(self):
            data = {
                "id": "upstream",
                "model": model,
                "usage": {"input_tokens": 10, "output_tokens": 2},
                "output": [
                    {
                        "type": "function_call",
                        "name": "choose_action",
                        "arguments": json.dumps({"candidate_id": "resupply"}),
                    }
                ],
            }
            return SimpleNamespace(model_dump=lambda **kwargs: data)

    async def create(**kwargs):
        calls.append(kwargs)
        return Raw()

    return SimpleNamespace(
        responses=SimpleNamespace(with_raw_response=SimpleNamespace(create=create))
    ), calls


async def test_gateway_validates_effective_deployment_and_uses_one_common_contract(
    tmp_path,
):
    c, calls = client()
    store = Store(tmp_path / "budget.db")
    provider = GatewayProvider(store, c, gateway=gateway())
    assert (
        await provider.decide(Observation.model_validate(observation())) == "resupply"
    )
    assert len(calls) == 1
    assert calls[0]["model"] == "participant-a"
    assert calls[0]["tools"][0]["parameters"]["properties"]["candidate_id"]["enum"] == [
        "continue",
        "resupply",
    ]
    assert store.budget()["spent"] == 14


@pytest.mark.parametrize(
    "model,deployment",
    [
        ("other-model", "deployment-a"),
        ("model-a", "fallback-deployment"),
        ("model-a", None),
    ],
)
async def test_gateway_identity_mismatch_is_paid_but_never_used_or_retried(
    tmp_path, model, deployment
):
    c, calls = client(model, deployment)
    store = Store(tmp_path / "budget.db")
    provider = GatewayProvider(store, c, gateway=gateway())
    with pytest.raises(ValueError, match="model"):
        await provider.decide(Observation.model_validate(observation()))
    assert len(calls) == 1
    assert store.budget()["spent"] == 14
    assert store.budget()["reserved"] == 0


def test_run_and_monthly_limits_share_one_transactional_ledger(tmp_path):
    store = Store(tmp_path / "budget.db", cap=100)
    store.reserve("one", 60, "2026-11", run_id="run-a", run_cap=70)
    with pytest.raises(BudgetExceeded, match="run"):
        store.reserve("two", 20, "2026-11", run_id="run-a", run_cap=70)
    with pytest.raises(BudgetExceeded, match="monthly"):
        store.reserve("three", 60, "2026-11", run_id="run-b", run_cap=70)
    assert store.budget("2026-11")["reserved"] == 60


def test_gateway_rejects_decisions_with_unbounded_billable_output():
    with pytest.raises(ValueError, match="output"):
        GatewayConfiguration.model_validate(
            gateway().model_dump() | {"decision_api": "decisions"}
        )
