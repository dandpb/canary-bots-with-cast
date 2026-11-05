from test_protocol import observation

from canary_brain.controller import Controller
from canary_brain.provider import Proposal
from canary_brain.store import Store


async def test_plan_advances_only_after_terminal_matching_outcome(tmp_path):
    class Model:
        calls = 0

        async def decide(self, *args, **kwargs):
            return "continue"

        async def converse(self, *args, **kwargs):
            self.calls += 1
            return Proposal(
                "resupply" if self.calls == 1 else "hold", "Proposta prudente.", "low"
            )

    model = Model()
    store = Store(tmp_path / "state.db")
    sent = []
    controller = Controller(store, model, sent.append, mode="active")
    packet = observation()
    packet["mode"] = "active"
    packet["actions"].append(
        {"id": "hold", "action": "hold", "description": "Wait", "ttl_ms": 5000}
    )
    packet["messages"] = [
        {"id": "plan-1", "player_id": 9, "text": "Reabasteça e depois aguarde aqui."}
    ]
    await controller.handle(packet)
    await controller.drain()
    intent = next(item for item in sent if item["type"] == "intent")
    outcome = {
        "version": 1,
        "type": "outcome",
        "world": intent["world"],
        "bot_id": intent["bot_id"],
        "action_id": intent["action_id"],
        "status": "accepted",
        "reason": "started",
        "metrics": {},
    }
    await controller.handle(outcome)
    packet["messages"] = []
    packet["objective_generation"] += 1
    await controller.handle(packet)
    await controller.drain()
    assert model.calls == 1
    outcome.update(status="completed", metrics={"elapsed_seconds": 20, "progress": 1})
    await controller.handle(outcome)
    await controller.handle(packet)
    await controller.drain()
    assert model.calls == 2
    assert [item["candidate_id"] for item in sent if item["type"] == "intent"] == [
        "resupply",
        "hold",
    ]


async def test_malformed_replan_cannot_repeat_a_paid_call_every_observation(tmp_path):
    class Model:
        calls = 0

        async def decide(self, *args, **kwargs):
            return "continue"

        async def converse(self, *args, **kwargs):
            self.calls += 1
            if self.calls > 1:
                raise ValueError("malformed provider tool output")
            return Proposal("resupply", "Proposta.", "low")

    model = Model()
    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), model, sent.append, mode="active"
    )
    packet = observation()
    packet["mode"] = "active"
    packet["messages"] = [
        {"id": "plan-1", "player_id": 9, "text": "Reabasteça e depois aguarde."}
    ]
    await controller.handle(packet)
    await controller.drain()
    intent = next(item for item in sent if item["type"] == "intent")
    await controller.handle(
        {
            "version": 1,
            "type": "outcome",
            "world": intent["world"],
            "bot_id": intent["bot_id"],
            "action_id": intent["action_id"],
            "status": "completed",
            "reason": "supplies_bought_and_party_rejoined",
            "metrics": {"elapsed_seconds": 20, "progress": 1},
        }
    )
    packet["messages"] = []
    for _ in range(8):
        await controller.handle(packet)
        await controller.drain()
    assert model.calls == 2
