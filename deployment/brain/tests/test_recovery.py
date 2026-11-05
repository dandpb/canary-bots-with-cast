import asyncio

from test_protocol import observation

from canary_brain.controller import Controller
from canary_brain.learning import Policy
from canary_brain.store import Store


def test_checkpoint_rollback_preserves_financial_and_character_independence(tmp_path):
    store = Store(tmp_path / "state.db")
    policy = Policy(store)
    policy.learn(1, "small-party", "hunt:1", 1)
    policy.checkpoint("before-change")
    store.reserve("charged", 100, "2026-11")
    policy.learn(1, "small-party", "hunt:1", 0)
    assert policy.statistics(1, "small-party")["hunt:1"]["count"] == 2
    policy.rollback("before-change")
    assert policy.statistics(1, "small-party")["hunt:1"]["count"] == 1
    assert store.budget("2026-11")["reserved"] == 100


async def test_terminal_outcome_is_learned_once_across_restart(tmp_path):
    class Model:
        async def decide(self, *args, **kwargs):
            return "resupply"

    store = Store(tmp_path / "state.db")
    sent = []
    controller = Controller(store, Model(), sent.append, mode="active")
    packet = observation()
    packet["mode"] = "active"
    await controller.handle(packet)
    await controller.drain()
    intent = next(item for item in sent if item["type"] == "intent")
    outcome = {
        "version": 1,
        "type": "outcome",
        "world": intent["world"],
        "bot_id": intent["bot_id"],
        "action_id": intent["action_id"],
        "status": "completed",
        "reason": "supplies_bought_and_party_rejoined",
        "metrics": {"elapsed_seconds": 20, "progress": 1},
    }
    await controller.handle(outcome)
    restarted = Controller(Store(store.path), Model(), sent.append, mode="active")
    await restarted.handle(outcome)
    data = store.records("policy")[0][1]
    assert data["actions"]["resupply"]["count"] == 1
    assert store.records("pending") == []


def test_atomic_records_roll_back_together_after_failure(tmp_path):
    store = Store(tmp_path / "state.db")
    try:
        with store.atomic():
            store.put("episode", "1", {"terminal": True})
            store.put("policy", "1", {"count": 1})
            raise RuntimeError("simulated interruption")
    except RuntimeError:
        pass
    assert store.get("episode", "1") is None
    assert store.get("policy", "1") is None


async def test_newer_leader_message_supersedes_old_slow_order(tmp_path):
    ready = asyncio.Event()

    class Model:
        async def decide(self, *args, **kwargs):
            return "continue"

        async def converse(self, *args, **kwargs):
            from canary_brain.provider import Proposal

            await ready.wait()
            return Proposal("resupply", "Vou reabastecer.", "low")

    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), Model(), sent.append, mode="active"
    )
    packet = observation()
    packet["mode"] = "active"
    packet["messages"] = [{"id": "old", "player_id": 9, "text": "comprar"}]
    await controller.handle(packet)
    await asyncio.sleep(0)
    packet["messages"].append({"id": "new", "player_id": 9, "text": "cancele, fique"})
    await controller.handle(packet)
    ready.set()
    await controller.drain()
    assert not any(item["type"] == "intent" for item in sent)


async def test_engine_restart_retries_cancelled_supply_goal_without_success_cooldown(
    tmp_path,
):
    from test_protocol import observation

    from canary_brain.controller import Controller

    class Model:
        async def decide(self, *args):
            return "resupply"

    path = tmp_path / "restart.db"
    first_sent, next_sent = [], []
    first = Controller(Store(path), Model(), first_sent.append, mode="active")
    packet = observation()
    packet["mode"] = "active"
    await first.handle(packet)
    await first.drain()
    await first.close()
    second = Controller(Store(path), Model(), next_sent.append, mode="active")
    packet["world"] = "restarted-engine"
    await second.handle(packet)
    await second.drain()
    assert any(item.get("candidate_id") == "resupply" for item in next_sent)
