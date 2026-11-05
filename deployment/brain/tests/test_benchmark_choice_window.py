import time

from test_protocol import observation

from canary_brain.benchmark_stops import Stops
from canary_brain.controller import Controller
from canary_brain.protocol import Observation
from canary_brain.store import Store
from canary_brain.testing import FakeProvider


async def test_a_choice_removed_from_the_sent_catalog_does_not_close_the_window(
    tmp_path,
):
    stops = Stops()
    events = []
    sent = []

    class InspectController(Controller):
        def record(self, bot, kind, data, key=None):
            events.append(data)
            super().record(bot, kind, data, key)

    controller = InspectController(
        Store(tmp_path / "state.db"),
        FakeProvider(),
        sent.append,
        mode="active",
        memory_mode="frozen",
        benchmark_stops=stops,
    )
    packet = observation()
    packet.update(party=None, autonomous=True)
    packet["bot"].update(health=100, objective_running=False)
    packet["actions"].append(
        {"id": "hunt:399", "action": "hunt", "description": "hunt", "ttl_ms": 5000}
    )
    snapshot = Observation.model_validate(packet)
    controller.latest[snapshot.bot.id] = snapshot
    stops.observe(snapshot.model_dump(), time.monotonic())
    try:
        # Fake proposes continue, which is deliberately removed from the actual
        # autonomous-work request although it still exists in raw observations.
        await controller._decide(snapshot)
    except ValueError:
        pass
    assert not any(e.get("phase") == "selected" for e in events), events
    assert stops.opportunity is not None
    fresh = snapshot.model_dump()
    fresh["sequence"] += 1
    stops.observe(fresh, stops.opportunity + 31)
    assert stops.check(stops.opportunity + 31) == "proposal_timeout"
    assert sent == []
