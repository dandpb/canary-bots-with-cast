import asyncio
from types import SimpleNamespace

import pytest
from canary_brain.protocol import Observation
from canary_brain.provider import Provider
from canary_brain.store import Store
from test_protocol import observation


@pytest.mark.parametrize(
    "answer,model",
    [
        ([], "gpt-6-luna"),
        ([{"name": "action", "type": "choice", "choice": "teleport"}], "gpt-6-luna"),
        ([{"name": "action", "type": "refusal"}], "gpt-6-luna"),
        ([{"name": "action", "type": "choice", "choice": "resupply"}], "other-model"),
    ],
)
async def test_unusable_answers_are_paid_but_never_applied(tmp_path, answer, model):
    async def create(**kwargs):
        return SimpleNamespace(
            model_dump=lambda **kw: {
                "model": model,
                "answers": answer,
                "usage": {
                    "input_tokens": 100,
                    "input_tokens_details": {
                        "cached_tokens": 20,
                        "cache_write_tokens": 10,
                    },
                },
            }
        )

    store = Store(tmp_path / "state.db")
    provider = Provider(
        store, SimpleNamespace(decisions=SimpleNamespace(create=create))
    )
    with pytest.raises(ValueError):
        await provider.decide(Observation.model_validate(observation()))
    assert store.budget()["spent"] == 8450
    assert store.budget()["reserved"] == 0


async def test_timeout_retains_reservation_and_backoff_prevents_retry_burst(tmp_path):
    calls = []

    async def create(**kwargs):
        calls.append(kwargs)
        await asyncio.sleep(1)

    store = Store(tmp_path / "state.db")
    provider = Provider(
        store,
        SimpleNamespace(decisions=SimpleNamespace(create=create)),
        decision_timeout=0.01,
    )
    with pytest.raises(TimeoutError):
        await provider.decide(Observation.model_validate(observation()))
    assert store.budget()["reserved"] > 0
    reserved = store.budget()["reserved"]
    with pytest.raises(RuntimeError):
        await provider.decide(Observation.model_validate(observation()))
    assert len(calls) == 1
    assert store.budget()["reserved"] == reserved


async def test_tool_result_is_correlated_and_reasoning_output_is_charged(tmp_path):
    calls = []

    async def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            model_dump=lambda **kw: {
                "model": "gpt-6-luna",
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 200,
                    "output_tokens_details": {"reasoning_tokens": 150},
                },
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "A compra falhou; faltou dinheiro.",
                            }
                        ],
                    }
                ],
            }
        )

    store = Store(tmp_path / "state.db")
    provider = Provider(
        store, SimpleNamespace(responses=SimpleNamespace(create=create))
    )
    result = await provider.reflect(
        {
            "type": "function_call",
            "name": "propose_objective",
            "call_id": "call-123",
            "arguments": '{"candidate_id":"resupply","reply":"Proposta"}',
        },
        {"status": "failed", "reason": "insufficient_funds"},
    )
    assert "falhou" in result
    assert calls[0]["input"][1]["call_id"] == "call-123"
    assert store.budget()["spent"] == 110000
