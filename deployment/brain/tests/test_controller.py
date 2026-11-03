import asyncio

from canary_brain.controller import Controller
from canary_brain.provider import Proposal
from canary_brain.store import Store
from test_protocol import observation


async def test_former_leader_cannot_apply_a_slow_response_after_transfer(tmp_path):
    ready = asyncio.Event()

    class Model:
        async def converse(self, *args, **kwargs):
            await ready.wait()
            return Proposal("resupply", "Vou propor reabastecer.", "low")

        async def decide(self, *args, **kwargs):
            return "continue"

    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), Model(), sent.append, mode="active"
    )
    initial = observation()
    initial["mode"] = "active"
    initial["messages"] = [
        {"id": "message-1", "player_id": 9, "text": "Comprar pocoes"}
    ]
    await controller.handle(initial)
    await asyncio.sleep(0)
    changed = observation()
    changed["party"]["leader_id"] = 10
    changed["objective_generation"] = 3
    changed["mode"] = "active"
    await controller.handle(changed)
    ready.set()
    await controller.drain()
    assert not any(
        packet.get("type") == "intent" and packet.get("candidate_id") == "resupply"
        for packet in sent
    )


async def test_lost_acknowledgement_retries_the_same_action_identity(
    tmp_path, monkeypatch
):
    clock = [1.0]
    monkeypatch.setattr("canary_brain.controller.time.monotonic", lambda: clock[0])

    class Model:
        async def decide(self, *args, **kwargs):
            return "resupply"

    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), Model(), sent.append, mode="active"
    )
    packet = observation()
    packet["mode"] = "active"
    await controller.handle(packet)
    await controller.drain()
    first = next(item for item in sent if item["type"] == "intent")
    clock[0] = 2.1
    controller.reconcile()
    retried = [item for item in sent if item["type"] == "intent"]
    assert len(retried) == 2
    assert retried[0]["action_id"] == retried[1]["action_id"] == first["action_id"]
