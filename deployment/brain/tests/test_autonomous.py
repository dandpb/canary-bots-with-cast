from canary_brain.controller import Controller
from canary_brain.provider import Proposal
from canary_brain.store import Store
from test_protocol import observation


async def test_special_bot_decides_without_party_and_accepts_any_human(tmp_path):
    calls = []

    class Model:
        async def decide(self, snapshot, memory):
            calls.append("decision")
            return "resupply"

        async def converse(self, snapshot, text, authorized, *args):
            calls.append(("responses", authorized))
            return Proposal("resupply", "Vou reabastecer.", "low")

    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), Model(), sent.append, mode="active"
    )
    packet = observation()
    packet.update(party=None, autonomous=True, mode="active")
    await controller.handle(packet)
    await controller.drain()
    assert "decision" in calls
    assert any(item.get("candidate_id") == "resupply" for item in sent)
    sent.clear()
    packet["messages"] = [{"id": "outside-1", "player_id": 123, "text": "reabasteça"}]
    await controller.handle(packet)
    await controller.drain()
    assert ("responses", True) in calls
    assert any(item.get("candidate_id") == "resupply" for item in sent)


async def test_ordinary_solo_bot_cannot_receive_objectives(tmp_path):
    class Model:
        async def converse(self, snapshot, text, authorized, *args):
            assert not authorized
            return Proposal("resupply", "Preciso de uma party.", "low")

        async def decide(self, *args):
            raise AssertionError("ordinary solo bot must retain native AI")

    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), Model(), sent.append, mode="active"
    )
    packet = observation()
    packet.update(party=None, mode="active")
    packet["messages"] = [{"id": "outside-1", "player_id": 123, "text": "reabasteça"}]
    await controller.handle(packet)
    await controller.drain()
    assert not any(item.get("type") == "intent" for item in sent)


async def test_special_bot_avoids_three_identical_hunts_even_with_global_learning_off(
    tmp_path,
):
    class Model:
        async def decide(self, *args):
            return "hunt:399"

        async def converse(self, *args):
            return Proposal("continue", "Explorar com cuidado.", "low")

    sent = []
    state = tmp_path / "state.db"
    selected = []
    for round_number in range(4):
        # A new process must retain the recent experiences.
        controller = Controller(
            Store(state), Model(), sent.append, mode="active", learning=False
        )
        packet = observation()
        packet.update(autonomous=True, mode="active", objective_generation=round_number)
        packet["actions"] = [packet["actions"][0]] + [
            {
                "id": f"hunt:{hunt}",
                "action": "hunt",
                "description": "Suitable local hunt",
                "ttl_ms": 5000,
            }
            for hunt in (399, 548)
        ]
        await controller.handle(packet)
        await controller.drain()
        intent = [item for item in sent if item.get("type") == "intent"][-1]
        selected.append(intent["candidate_id"])
        await controller.handle(
            {
                "version": 1,
                "type": "outcome",
                "world": packet["world"],
                "bot_id": 7,
                "action_id": intent["action_id"],
                "status": "completed",
                "reason": "hunt_progress",
                "metrics": {
                    "elapsed_seconds": 300.0,
                    "xp_delta": 500.0,
                    "level": 80.0,
                    "party_size": 2.0,
                    "progress": 1.0,
                },
            }
        )
        await controller.close()
    assert len(set(selected)) == 2
    assert selected != ["hunt:399"] * 4


async def test_idle_explorer_does_not_keep_continuing_an_empty_objective(tmp_path):
    class Model:
        async def decide(self, snapshot, memory):
            return (
                "continue"
                if any(item.id == "continue" for item in snapshot.actions)
                else "resupply"
            )

        async def converse(self, *args):
            return Proposal("continue", "Reabastecer antes de explorar.", "low")

    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), Model(), sent.append, mode="active"
    )
    packet = observation()
    packet.update(party=None, autonomous=True, mode="active")
    await controller.handle(packet)
    await controller.drain()
    assert any(item.get("candidate_id") == "resupply" for item in sent)


async def test_healthy_solo_explorer_does_not_retreat_repeatedly_without_threats(
    tmp_path,
):
    class Model:
        async def decide(self, snapshot, memory):
            return (
                "retreat"
                if any(item.id == "retreat" for item in snapshot.actions)
                else "resupply"
            )

        async def converse(self, *args):
            return Proposal("continue", "Explorar com prudência.", "low")

    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), Model(), sent.append, mode="active"
    )
    packet = observation()
    packet.update(party=None, autonomous=True, mode="active")
    packet["actions"].append(
        {
            "id": "retreat",
            "action": "retreat",
            "description": "Return home",
            "ttl_ms": 1500,
        }
    )
    await controller.handle(packet)
    await controller.drain()
    assert any(item.get("candidate_id") == "resupply" for item in sent)


async def test_first_goal_is_preceded_by_a_heartbeat_for_the_new_engine(tmp_path):
    class Model:
        async def decide(self, *args):
            return "resupply"

    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), Model(), sent.append, mode="active"
    )
    packet = observation()
    packet["mode"] = "active"
    await controller.handle(packet)
    await controller.drain()
    assert [item["type"] for item in sent][:2] == ["heartbeat", "intent"]


async def test_idle_explorer_returns_from_a_floor_without_available_work(tmp_path):
    class Model:
        async def decide(self, snapshot, memory):
            return (
                "continue"
                if any(a.id == "continue" for a in snapshot.actions)
                else "retreat"
            )

        async def converse(self, *args):
            return Proposal(
                "retreat", "Voltar à cidade para escolher outra atividade.", "low"
            )

    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), Model(), sent.append, mode="active"
    )
    packet = observation()
    packet.update(party=None, autonomous=True, mode="active")
    packet["bot"].update(
        state="IDLE", objective_running=False, position=[100, 100, 8], potions=40
    )
    packet["actions"] = [
        packet["actions"][0],
        {
            "id": "retreat",
            "action": "retreat",
            "description": "Return to town for the next activity",
            "ttl_ms": 1500,
        },
    ]
    await controller.handle(packet)
    await controller.drain()
    assert any(item.get("candidate_id") == "retreat" for item in sent)
    await controller.close()
