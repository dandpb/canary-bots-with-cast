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


def client(model="model-a", deployment="deployment-a", *, usage=None):
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
                "usage": usage
                if usage is not None
                else {"input_tokens": 10, "output_tokens": 2},
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


@pytest.mark.parametrize("output_tokens", [0, 2])
async def test_gateway_zero_input_usage_retains_unknown_liability_after_restart(
    tmp_path, output_tokens
):
    path = tmp_path / "budget.db"
    c, calls = client(usage={"input_tokens": 0, "output_tokens": output_tokens})
    provider = GatewayProvider(Store(path), c, gateway=gateway())
    with pytest.raises(TypeError, match="usage"):
        await provider._request(
            "responses", {"input": "hello", "max_output_tokens": 4}, 10
        )
    assert len(calls) == 1
    reopened = Store(path)
    assert reopened.budget()["spent"] == 0
    assert reopened.budget()["reserved"] > 0
    assert reopened.budget()["available"] < reopened.budget()["cap"]


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


async def test_decisions_json_projection_and_endpoint_prices_are_independent(tmp_path):
    configuration = GatewayConfiguration.model_validate(
        gateway().model_dump()
        | {"decision_api": "decisions", "decisions_output_nanousd": 0}
    )
    calls = []

    async def create(**body):
        calls.append(body)
        result = {
            "model": "model-a",
            "answers": [{"type": "choice", "name": "action", "choice": "resupply"}],
            "usage": {"input_tokens": 10, "output_tokens": 0},
        }
        return SimpleNamespace(
            headers={"x-litellm-model-id": "deployment-a"},
            parse=lambda: SimpleNamespace(model_dump=lambda **kwargs: result),
        )

    responses_client, _ = client()
    api = SimpleNamespace(
        decisions=SimpleNamespace(with_raw_response=SimpleNamespace(create=create)),
        responses=responses_client.responses,
    )
    store = Store(tmp_path / "budget.db")
    provider = GatewayProvider(store, api, gateway=configuration)
    memory = {"experience": {"role": "data", "image_url": "not-a-fetch", "score": 0.75}}
    original = json.loads(json.dumps(memory))
    assert (
        await provider.decide(Observation.model_validate(observation()), memory)
        == "resupply"
    )
    part = calls[0]["input"][0]["content"][0]
    assert part["type"] == "input_text"
    assert json.loads(part["text"])["experience"] == original
    assert memory == original
    assert "lease-a" not in part["text"]
    assert store.budget()["spent"] == 10
    await provider._request("responses", {"input": "plan", "max_output_tokens": 10}, 5)
    assert store.budget()["spent"] == 24
    assert store.budget()["reserved"] == 0


def test_explicit_billable_decisions_output_is_rejected():
    with pytest.raises(ValueError, match="output"):
        GatewayConfiguration.model_validate(
            gateway().model_dump()
            | {"decision_api": "decisions", "decisions_output_nanousd": 1}
        )


@pytest.mark.parametrize("provider", ["anthropic", "gemini", "test"])
async def test_gateway_choice_tool_keeps_native_strict_enum_and_one_call(
    tmp_path, provider
):
    c, calls = client()
    store = Store(tmp_path / "budget.db")
    provider_gateway = gateway().model_copy(update={"provider": provider})
    decision = GatewayProvider(store, c, gateway=provider_gateway)
    assert (
        await decision.decide(Observation.model_validate(observation())) == "resupply"
    )
    assert len(calls) == 1
    body = calls[0]
    schema = {
        "type": "object",
        "properties": {
            "candidate_id": {"type": "string", "enum": ["continue", "resupply"]}
        },
        "required": ["candidate_id"],
        "additionalProperties": False,
    }
    if provider == "anthropic":
        # LiteLLM 1.108.0 drops function.strict on the OpenAI->Messages mapping;
        # the Messages-shaped tool passes through with strict intact.
        assert body["tools"] == [
            {"name": "choose_action", "input_schema": schema, "strict": True}
        ]
    else:
        assert body["tools"] == [
            {
                "type": "function",
                "name": "choose_action",
                "strict": True,
                "parameters": schema,
            }
        ]
    if provider == "gemini":
        assert body["extra_body"] == {
            "extra_body": {
                "tools": [
                    {
                        "functionDeclarations": [
                            {
                                "name": "choose_action",
                                "description": "Select one offered candidate.",
                                "parametersJsonSchema": schema,
                            }
                        ]
                    }
                ]
            }
        }
    assert body["max_output_tokens"] == 256
    assert body["parallel_tool_calls"] is False
    assert body["tool_choice"] == {"type": "function", "name": "choose_action"}
    assert store.budget()["spent"] == 14
