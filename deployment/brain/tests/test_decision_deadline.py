import asyncio
from types import SimpleNamespace

import pytest
from test_gateway import client, gateway
from test_protocol import observation

from canary_brain.gateway import GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.provider import Provider, ProviderBackoff
from canary_brain.store import Store


def recorder(events):
    return SimpleNamespace(
        manifests={}, emit=lambda bot, kind, data, key=None: events.append(data)
    )


async def test_expired_combat_choice_does_not_back_off_the_next_objective(tmp_path):
    fake, calls = client()
    reply = fake.responses.with_raw_response.create

    async def respond(**request):
        if "target:123" in str(request["input"]):
            await asyncio.sleep(1)
        return await reply(**request)

    fake.responses.with_raw_response.create = respond
    store = Store(tmp_path / "state.db")
    provider = GatewayProvider(store, fake, 1, gateway=gateway())
    tactical = observation()
    tactical["actions"][1] = {
        "id": "target:123",
        "action": "target",
        "description": "Preferred nearby monster",
        "ttl_ms": 100,
    }
    with pytest.raises(TimeoutError):
        await provider.decide(Observation.model_validate(tactical))
    with pytest.raises(ProviderBackoff):
        await provider.decide(Observation.model_validate(tactical))

    assert (
        await provider.decide(Observation.model_validate(observation())) == "resupply"
    )
    assert len(calls) == 1
    assert store.budget()["spent"] > 0 and store.budget()["reserved"] > 0


def slow_provider(tmp_path, events, seconds):
    async def create(**kwargs):
        await asyncio.sleep(seconds)

    store = Store(tmp_path / "state.db")
    provider = Provider(
        store,
        SimpleNamespace(decisions=SimpleNamespace(create=create)),
        decision_timeout=0.05,
        recorder=recorder(events),
    )
    return store, provider


async def test_deadline_miss_is_recorded_as_timeout_and_keeps_its_liability(
    tmp_path,
):
    events = []
    store, provider = slow_provider(tmp_path, events, 1)
    with pytest.raises(TimeoutError):
        await provider.decide(Observation.model_validate(observation()))
    [(_, record)] = store.records("request")
    assert record["error"] == "TimeoutError"
    assert record["deadline_ms"] == 50 and record["unsettled"] is True
    reserved, failed = events
    assert reserved["deadline_ms"] == 50
    assert failed["phase"] == "failed" and failed["error"] == "TimeoutError"
    assert failed["deadline_ms"] == 50
    assert failed["reserved_nanousd"] == reserved["reserved_nanousd"]
    # A late answer is discarded: its upper bound stays an unknown liability.
    assert store.budget()["spent"] == 0
    assert store.budget()["reserved"] == reserved["reserved_nanousd"]


async def test_external_cancellation_is_not_counted_as_a_deadline_miss(tmp_path):
    events = []
    store, provider = slow_provider(tmp_path, events, 1)
    provider.decision_timeout = 5
    task = asyncio.create_task(
        provider.decide(Observation.model_validate(observation()))
    )
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert store.records("request")[0][1]["error"] == "CancelledError"
    assert store.budget()["reserved"] > 0


@pytest.mark.parametrize(
    "configured,ttls,applied",
    [
        (1.2, (5000, 5000), 1.2),
        (2.5, (5000, 5000), 2.5),
        (10, (5000, 5000), 5.0),
        (2.5, (1500, 5000), 1.5),
        (10, (1000, 5000), 1.0),
    ],
)
async def test_configured_gateway_deadline_is_capped_by_the_server_ttl(
    tmp_path, configured, ttls, applied
):
    seen = []

    class Probe(GatewayProvider):
        async def _request(
            self, endpoint, body, timeout, *, fast=False, tactical=False
        ):
            seen.append(timeout)
            return await super()._request(
                endpoint, body, timeout, fast=fast, tactical=tactical
            )

    fake, _ = client()
    packet = observation()
    for action, ttl in zip(packet["actions"], ttls, strict=True):
        action["ttl_ms"] = ttl
    provider = Probe(Store(tmp_path / "state.db"), fake, configured, gateway=gateway())
    assert await provider.decide(Observation.model_validate(packet)) == "resupply"
    assert seen == [applied]
