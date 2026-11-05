import json

from test_protocol import observation
from test_recording import recorder

from canary_brain.controller import Controller
from canary_brain.recording import ReplayReader
from canary_brain.store import Store
from canary_brain.testing import FakeProvider


async def test_real_controller_records_proposals_intents_and_duplicate_outcomes_once(
    tmp_path,
):
    r = recorder(tmp_path)
    sent = []
    c = Controller(
        Store(tmp_path / "state.db"),
        FakeProvider(),
        sent.append,
        mode="active",
        recorder=r,
    )
    packet = observation()
    packet["mode"] = "active"
    packet["messages"] = [{"id": "m1", "player_id": 9, "text": "comprar pocoes"}]
    await c.handle(packet)
    await c.drain()
    intent = next(p for p in sent if p["type"] == "intent")
    outcome = {
        "version": 1,
        "type": "outcome",
        "world": "world-a",
        "bot_id": 7,
        "action_id": intent["action_id"],
        "status": "completed",
        "reason": "supplies_bought",
        "metrics": {},
    }
    await c.handle(outcome)
    await c.handle(outcome)
    await c.close()
    r.close()
    events = list(ReplayReader(r.config.path).all_events("qa:7"))
    assert len([e for e in events if e["kind"] == "outcome"]) == 1
    assert any(e["kind"] == "intent" for e in events)
    assert any(e["kind"] == "proposal" for e in events)
    assert "lease-a" not in json.dumps(events)
