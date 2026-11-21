import asyncio

import pytest
from test_protocol import observation

from canary_brain.controller import Controller
from canary_brain.provider import Proposal
from canary_brain.recording import RecordingConfiguration
from canary_brain.runtime import Configuration
from canary_brain.store import Store


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


async def test_dynamic_human_party_admits_up_to_cap_and_evicts_non_party(tmp_path):
    class Model:
        async def decide(self, *args, **kwargs):
            return "resupply"

        async def converse(self, *args, **kwargs):
            return Proposal("continue", "ok", "low")

    sent = []
    controller = Controller(
        Store(tmp_path / "dynamic.db"),
        Model(),
        sent.append,
        mode="active",
        roster={65001},
        dynamic_human_party=True,
        max_active_bots=13,
    )

    for offset in range(10):
        bot_id = 65100 + offset
        pkt = observation()
        pkt["mode"] = "active"
        pkt["bot"]["id"] = bot_id
        pkt["party"] = {"leader_id": 9, "members": [9, bot_id]}
        await controller.handle(pkt)

    # Non-roster solo bot must still be ignored under dynamic_human_party.
    solo = observation()
    solo["mode"] = "active"
    solo["bot"]["id"] = 65999
    solo["party"] = None
    solo["autonomous"] = False
    await controller.handle(solo)

    await controller.drain()
    assert len(controller.latest) == 10
    assert 65999 not in controller.latest
    assert len({item["bot_id"] for item in sent if item.get("type") == "intent"}) == 10

    # Leaving the human party evicts the dynamic bot cleanly from latest.
    left = observation()
    left["mode"] = "active"
    left["bot"]["id"] = 65100
    left["party"] = None
    await controller.handle(left)
    assert 65100 not in controller.latest

    # Backward compatibility: with dynamic_human_party=False, non-roster party bots are rejected.
    static_ctrl = Controller(
        Store(tmp_path / "static.db"),
        Model(),
        sent.append,
        mode="active",
        roster={65001},
    )
    non_roster_party = observation()
    non_roster_party["mode"] = "active"
    non_roster_party["bot"]["id"] = 65105
    await static_ctrl.handle(non_roster_party)
    assert 65105 not in static_ctrl.latest


def test_runtime_configuration_validates_dynamic_human_party(tmp_path):
    cfg = Configuration(
        socket_directory=tmp_path / "sock",
        state_file=tmp_path / "state.db",
        bots=[65001, 65004, 65003],
        dynamic_human_party=True,
        max_human_party_bots=10,
    )
    assert cfg.dynamic_human_party is True
    assert cfg.max_human_party_bots == 10

    with pytest.raises(ValueError):
        Configuration(
            socket_directory=tmp_path / "sock2",
            state_file=tmp_path / "state2.db",
            bots=[65001],
            dynamic_human_party=True,
            max_human_party_bots=11,
        )

    with pytest.raises(ValueError, match="dynamic_human_party"):
        Configuration(
            socket_directory=tmp_path / "sock3",
            state_file=tmp_path / "state3.db",
            bots=[65001],
            dynamic_human_party=True,
            recording=RecordingConfiguration(
                path=tmp_path / "rec.db",
                namespace="test",
            ),
        )
