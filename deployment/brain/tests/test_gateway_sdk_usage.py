"""Real OpenAI SDK parsing must distinguish omitted counters from explicit null."""

import json

import httpx2 as httpx
import pytest
from openai import AsyncOpenAI
from test_gateway import gateway
from test_protocol import observation

from canary_brain.gateway import GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.store import Store


@pytest.mark.parametrize("counter", ["omitted", 0, None])
async def test_gemini_sdk_optional_write_counter_does_not_synthesize_usage(
    tmp_path, counter
):
    details = {"cached_tokens": 0}
    if counter != "omitted":
        details["cache_write_tokens"] = counter

    def respond(request):
        return httpx.Response(
            200,
            headers={"x-litellm-model-id": "deployment-a"},
            json={
                "id": "response-fixture",
                "created_at": 0,
                "object": "response",
                "model": "model-a",
                "tools": [],
                "tool_choice": "auto",
                "parallel_tool_calls": False,
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc-fixture",
                        "call_id": "call-fixture",
                        "name": "choose_action",
                        "arguments": json.dumps({"candidate_id": "resupply"}),
                    }
                ],
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 2,
                    "total_tokens": 12,
                    "input_tokens_details": details,
                },
            },
        )

    store = Store(tmp_path / "budget.sqlite3")
    config = gateway().model_copy(update={"provider": "gemini"})
    async with AsyncOpenAI(
        api_key="synthetic-only",
        base_url="http://127.0.0.1:4000/v1",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
    ) as client:
        provider = GatewayProvider(store, client, gateway=config)
        if counter in {"omitted", 0}:
            assert (
                await provider.decide(Observation.model_validate(observation()))
                == "resupply"
            )
            assert store.budget()["spent"] == 14
            assert store.budget()["reserved"] == 0
        else:
            expected = TypeError if counter is None else ValueError
            with pytest.raises(expected):
                await provider.decide(Observation.model_validate(observation()))
            assert store.budget()["spent"] == 0
            assert store.budget()["reserved"] > 0
