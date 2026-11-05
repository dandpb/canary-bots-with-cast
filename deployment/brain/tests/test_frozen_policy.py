from canary_brain.controller import Controller
from canary_brain.store import Store
from test_protocol import observation


async def test_frozen_run_has_no_policy_override_updates_or_autonomous_memory_calls(
    tmp_path,
):
    class Model:
        async def decide(self, snapshot, memory):
            return "hunt:a"

        async def converse(self, *args, **kwargs):
            raise AssertionError(
                "a frozen trial must not create autonomous strategy memory"
            )

    store = Store(tmp_path / "state.db")
    sent = []
    controller = Controller(
        store, Model(), sent.append, mode="active", memory_mode="frozen"
    )
    packet = observation()
    packet.update(mode="active", autonomous=True, party=None)
    packet["actions"] = [
        {
            "id": "hunt:" + name,
            "action": "hunt",
            "description": "A safe hunt",
            "ttl_ms": 30000,
        }
        for name in ("a", "b")
    ]
    await controller.handle(packet)
    await controller.drain()
    action = next(item for item in sent if item["type"] == "intent")
    assert action["candidate_id"] == "hunt:a"
    await controller.handle(
        {
            "version": 1,
            "type": "outcome",
            "world": packet["world"],
            "action_id": action["action_id"],
            "bot_id": 7,
            "status": "completed",
            "reason": "hunt_progress",
            "metrics": {
                "progress": 1.0,
                "xp_delta": 100.0,
                "defeats_delta": 2.0,
                "elapsed_seconds": 300.0,
                "deaths": 0.0,
            },
        }
    )
    assert not store.records("policy")
    assert not store.records("autonomous_strategy")
    await controller.close()
