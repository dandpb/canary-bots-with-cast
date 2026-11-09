"""OpenAI decision effort is opt-in and survives the real SDK wire mapping."""

import json
from contextlib import asynccontextmanager

import httpx2 as httpx
import pytest
from openai import AsyncOpenAI
from test_gateway import gateway
from test_protocol import observation

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.store import Store


def configuration(**changes):
    return GatewayConfiguration.model_validate(
        gateway().model_dump() | {"provider": "openai"} | changes
    )


@asynccontextmanager
async def sdk(response=None):
    requests = []

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        name = body.get("tool_choice", {}).get("name", "choose_action")
        arguments = {"candidate_id": "resupply"}
        if name == "propose_objective":
            arguments["reply"] = "Vou reabastecer."
        data = {
            "id": "offline-response",
            "created_at": 0,
            "object": "response",
            "model": "model-a",
            "status": "completed",
            "tools": [],
            "tool_choice": "auto",
            "parallel_tool_calls": False,
            "output": [
                {
                    "type": "function_call",
                    "id": "offline-function",
                    "call_id": "offline-call",
                    "name": name,
                    "arguments": json.dumps(arguments),
                }
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 2,
                "total_tokens": 12,
            },
        }
        if response is not None:
            data.update(response)
        return httpx.Response(
            200, headers={"x-litellm-model-id": "deployment-a"}, json=data
        )

    async with AsyncOpenAI(
        api_key="synthetic-only",
        base_url="http://127.0.0.1:4000/v1",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
    ) as client:
        yield client, requests


async def test_explicit_none_reaches_sdk_wire_without_weakening_the_choice(tmp_path):
    store = Store(tmp_path / "synthetic.db")
    async with sdk() as (client, requests):
        provider = GatewayProvider(
            store, client, gateway=configuration(decision_reasoning_effort="none")
        )
        assert (
            await provider.decide(Observation.model_validate(observation()))
            == "resupply"
        )
    assert len(requests) == 1
    assert requests[0]["reasoning"] == {"effort": "none"}
    assert requests[0]["max_output_tokens"] == 256
    assert requests[0]["tools"][0]["strict"] is True
    assert requests[0]["parallel_tool_calls"] is False
    assert requests[0]["tool_choice"] == {"type": "function", "name": "choose_action"}
    assert store.budget()["spent"] == 14


@pytest.mark.parametrize("effort", [None, "low", "medium", "high", "xhigh", "max"])
async def test_decision_effort_is_omitted_by_default_or_sent_explicitly(
    tmp_path, effort
):
    changes = {} if effort is None else {"decision_reasoning_effort": effort}
    async with sdk() as (client, requests):
        provider = GatewayProvider(
            Store(tmp_path / "synthetic.db"), client, gateway=configuration(**changes)
        )
        assert (
            await provider.decide(Observation.model_validate(observation()))
            == "resupply"
        )
    if effort is None:
        assert "reasoning" not in requests[0]
    else:
        assert requests[0]["reasoning"] == {"effort": effort}


@pytest.mark.parametrize(
    "changes",
    [
        {"provider": "gemini"},
        {"provider": "anthropic"},
        {"provider": "test"},
        {"decision_api": "decisions"},
        {"reasoning": True},
        {"decision_reasoning_effort": "minimal"},
    ],
)
def test_explicit_effort_rejects_unsupported_or_contradictory_configuration(changes):
    with pytest.raises(ValueError):
        configuration(**({"decision_reasoning_effort": "none"} | changes))


@pytest.mark.parametrize(
    "legacy,explicit,deep,expected",
    [
        (False, None, False, None),
        (True, None, False, {"effort": "low"}),
        (True, None, True, {"effort": "max"}),
        (False, "none", True, None),
    ],
)
async def test_decision_opt_in_preserves_legacy_conversation_reasoning(
    tmp_path, legacy, explicit, deep, expected
):
    async with sdk() as (client, requests):
        provider = GatewayProvider(
            Store(tmp_path / "synthetic.db"),
            client,
            gateway=configuration(reasoning=legacy, decision_reasoning_effort=explicit),
        )
        result = await provider.converse(
            Observation.model_validate(observation()), "reabastecer", True, deep=deep
        )
    assert result.candidate_id == "resupply"
    assert result.reply == "Vou reabastecer."
    assert requests[0].get("reasoning") == expected
    assert requests[0]["tool_choice"] == {
        "type": "function",
        "name": "propose_objective",
    }
    assert requests[0]["max_output_tokens"] == (4096 if deep else 768)
