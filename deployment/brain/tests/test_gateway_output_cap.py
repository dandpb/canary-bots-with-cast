"""Decision output headroom is opt-in, reserved first, and isolated from dialogue."""

import asyncio
import hashlib
import json
from contextlib import asynccontextmanager

import httpx2 as httpx
import pytest
from openai import APIConnectionError, AsyncOpenAI
from test_gateway_reasoning import configuration
from test_protocol import observation

from canary_brain.gateway import GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.provider import ProviderBackoff
from canary_brain.store import BudgetExceeded, Store


@asynccontextmanager
async def wire(store, *, response=None, error=False, delay=0):
    requests, reservations = [], []

    async def respond(request):
        requests.append(request.content)
        reservations.append(store.budget()["reserved"])
        if delay:
            await asyncio.sleep(delay)
        if error:
            raise httpx.ReadError("synthetic transport failure", request=request)
        body = json.loads(request.content)
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
        yield client, requests, reservations


@pytest.fixture(autouse=True)
def refuse_real_http(monkeypatch):
    async def reject(*args, **kwargs):
        raise AssertionError("this suite permits MockTransport only")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", reject)


@pytest.mark.parametrize("limit", [256, 1024, 2048, 4096])
def test_decision_output_cap_accepts_bounded_strict_integers(limit):
    assert (
        configuration(decision_max_output_tokens=limit).decision_max_output_tokens
        == limit
    )


@pytest.mark.parametrize("limit", [None, True, False, 0, 255, 4097, 2048.0, "2048"])
def test_decision_output_cap_rejects_invalid_or_coerced_values(limit):
    with pytest.raises(ValueError):
        configuration(decision_max_output_tokens=limit)


@pytest.mark.parametrize("provider", ["gemini", "anthropic", "test"])
def test_larger_decision_cap_rejects_other_providers(provider):
    with pytest.raises(ValueError, match="OpenAI Responses"):
        configuration(provider=provider, decision_max_output_tokens=2048)


def test_larger_decision_cap_rejects_unbounded_decisions_api():
    prices = configuration().prices.model_dump() | {"output_nanousd": 0}
    with pytest.raises(ValueError, match="OpenAI Responses"):
        configuration(
            decision_api="decisions", prices=prices, decision_max_output_tokens=2048
        )


@pytest.mark.parametrize("provider", ["openai", "gemini"])
async def test_default_and_explicit_legacy_cap_keep_identical_wire(tmp_path, provider):
    bodies = []
    for index, changes in enumerate([{}, {"decision_max_output_tokens": 256}]):
        store = Store(tmp_path / f"synthetic-{index}.db")
        async with wire(store) as (client, requests, _):
            gateway = configuration(provider=provider, **changes)
            assert gateway.decision_max_output_tokens == 256
            model = GatewayProvider(store, client, gateway=gateway)
            assert (
                await model.decide(Observation.model_validate(observation()))
                == "resupply"
            )
        assert len(requests) == 1
        bodies.append(requests[0])
        assert "reasoning" not in json.loads(requests[0])
        assert store.budget()["spent"] == 14
    assert bodies[0] == bodies[1]


async def test_larger_cap_reaches_sdk_before_reservation_and_keeps_default_reasoning(
    tmp_path,
):
    observations = Observation.model_validate(observation())
    runs = []
    for index, changes in enumerate([{}, {"decision_max_output_tokens": 2048}]):
        store = Store(tmp_path / f"synthetic-{index}.db")
        async with wire(store) as (client, requests, reservations):
            model = GatewayProvider(store, client, gateway=configuration(**changes))
            assert await model.decide(observations) == "resupply"
        assert len(requests) == 1
        body = json.loads(requests[0])
        assert "reasoning" not in body
        assert body["tool_choice"] == {"type": "function", "name": "choose_action"}
        assert body["parallel_tool_calls"] is False
        assert body["tools"][0]["strict"] is True
        assert reservations[0] > 0
        # The limit is a ceiling: settlement uses the returned 2 output tokens.
        assert store.budget()["spent"] == 14
        assert store.budget()["reserved"] == 0
        runs.append((body, reservations[0]))
    legacy, larger = runs
    assert legacy[0].pop("max_output_tokens") == 256
    assert larger[0].pop("max_output_tokens") == 2048
    assert legacy[0] == larger[0]
    # 1792 extra output tokens at 2 nanoUSD, plus one input byte for the cap.
    assert larger[1] - legacy[1] == 1792 * 2 + 1


async def test_budget_that_fits_legacy_cap_denies_larger_cap_before_sdk(tmp_path):
    store = Store(tmp_path / "legacy.db")
    async with wire(store) as (client, _, reservations):
        model = GatewayProvider(store, client, gateway=configuration())
        await model.decide(Observation.model_validate(observation()))
    smaller_budget = Store(tmp_path / "bounded.db", cap=reservations[0])
    async with wire(smaller_budget) as (client, requests, _):
        model = GatewayProvider(
            smaller_budget,
            client,
            gateway=configuration(decision_max_output_tokens=2048),
        )
        with pytest.raises(BudgetExceeded):
            await model.decide(Observation.model_validate(observation()))
    assert requests == []
    assert smaller_budget.budget()["reserved"] == 0
    assert smaller_budget.budget()["spent"] == 0


@pytest.mark.parametrize("failure", ["transport", "usage"])
async def test_larger_cap_retains_unknown_reservation_without_retry(tmp_path, failure):
    path = tmp_path / "unknown.db"
    store = Store(path)
    async with wire(
        store,
        response={"usage": None} if failure == "usage" else None,
        error=failure == "transport",
    ) as (client, requests, reservations):
        model = GatewayProvider(
            store, client, gateway=configuration(decision_max_output_tokens=2048)
        )
        expected = TypeError if failure == "usage" else APIConnectionError
        with pytest.raises(expected):
            await model.decide(Observation.model_validate(observation()))
    assert len(requests) == 1
    reopened = Store(path)
    assert reopened.budget()["spent"] == 0
    assert reopened.budget()["reserved"] == reservations[0] > 2048 * 2


async def test_larger_cap_timeout_keeps_reservation_and_existing_backoff(tmp_path):
    path = tmp_path / "timeout.db"
    store = Store(path)
    async with wire(store, delay=1) as (client, requests, _):
        model = GatewayProvider(
            store,
            client,
            gateway=configuration(decision_max_output_tokens=2048),
            decision_timeout=0.01,
        )
        with pytest.raises(TimeoutError):
            await model.decide(Observation.model_validate(observation()))
        reserved = store.budget()["reserved"]
        request_count = len(requests)
        with pytest.raises(ProviderBackoff):
            await model.decide(Observation.model_validate(observation()))
        assert len(requests) == request_count
    # Expiry may precede the SDK transport callback; it never proves a send.
    assert len(requests) <= 1
    reopened = Store(path)
    assert reopened.budget()["spent"] == 0
    assert reopened.budget()["reserved"] == reserved > 2048 * 2


async def test_reasoning_usage_is_not_added_to_total_output_twice(tmp_path):
    store = Store(tmp_path / "reasoning-usage.db")
    usage = {
        "input_tokens": 10,
        "output_tokens": 200,
        "output_tokens_details": {"reasoning_tokens": 150},
        "total_tokens": 210,
    }
    async with wire(store, response={"usage": usage}) as (client, requests, _):
        model = GatewayProvider(
            store, client, gateway=configuration(decision_max_output_tokens=2048)
        )
        await model.decide(Observation.model_validate(observation()))
    assert len(requests) == 1
    assert store.budget()["spent"] == 10 + 200 * 2
    assert store.budget()["reserved"] == 0


@pytest.mark.parametrize("deep,expected", [(False, 768), (True, 4096)])
async def test_decision_cap_does_not_change_dialogue_limits(tmp_path, deep, expected):
    store = Store(tmp_path / "dialogue.db")
    async with wire(store) as (client, requests, _):
        model = GatewayProvider(
            store, client, gateway=configuration(decision_max_output_tokens=2048)
        )
        result = await model.converse(
            Observation.model_validate(observation()), "reabastecer", True, deep=deep
        )
    assert result.candidate_id == "resupply"
    body = json.loads(requests[0])
    assert body["max_output_tokens"] == expected
    assert "reasoning" not in body


async def test_decision_cap_does_not_change_reflection_limit(tmp_path):
    store = Store(tmp_path / "reflection.db")
    response = {
        "output": [
            {
                "type": "message",
                "id": "offline-message",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": "O resultado foi registrado.",
                        "annotations": [],
                    }
                ],
            }
        ]
    }
    async with wire(store, response=response) as (client, requests, _):
        model = GatewayProvider(
            store, client, gateway=configuration(decision_max_output_tokens=2048)
        )
        result = await model.reflect(
            {
                "type": "function_call",
                "call_id": "offline-tool",
                "name": "propose_objective",
                "arguments": '{"candidate_id":"resupply","reply":"Proposta"}',
            },
            {"status": "completed"},
        )
    assert result == "O resultado foi registrado."
    body = json.loads(requests[0])
    assert body["max_output_tokens"] == 384
    assert "reasoning" not in body


async def test_larger_cap_does_not_turn_a_single_candidate_into_a_paid_request(
    tmp_path,
):
    store = Store(tmp_path / "local.db")
    packet = observation()
    packet["actions"] = packet["actions"][1:]
    async with wire(store) as (client, requests, _):
        model = GatewayProvider(
            store, client, gateway=configuration(decision_max_output_tokens=2048)
        )
        assert await model.decide(Observation.model_validate(packet)) == "resupply"
    assert requests == []
    assert store.budget()["spent"] == store.budget()["reserved"] == 0


@pytest.mark.parametrize("provider", ["openai", "gemini"])
async def test_legacy_wire_matches_frozen_sdk_body(tmp_path, provider):
    # SDK3.42.1 body hashes captured from base529f before this opt-in existed.
    expected = {
        "openai": "2b34e5a7b71fc8682c0f7f699e8ba64e575017c82ce3f979277614a6943c2eb8",
        "gemini": "8c0613feb1a6ee8e27c63ccad1befc97364457af19406ff123f864a99741a89a",
    }
    store = Store(tmp_path / "legacy-wire.db")
    async with wire(store) as (client, requests, _):
        model = GatewayProvider(store, client, gateway=configuration(provider=provider))
        await model.decide(Observation.model_validate(observation()))
    assert hashlib.sha256(requests[0]).hexdigest() == expected[provider]
