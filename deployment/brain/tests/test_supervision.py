import asyncio
import json

import pytest
from test_protocol import observation

from canary_brain.controller import Controller
from canary_brain.operator_http import OperatorServer
from canary_brain.protocol import Observation, Outcome
from canary_brain.provider import Proposal
from canary_brain.store import Store
from canary_brain.testing import FakeProvider


def console(tmp_path, monkeypatch):
    clock = [10000.0]
    monkeypatch.setattr("canary_brain.supervision.time.time", lambda: clock[0])
    sent = []
    controller = Controller(
        Store(tmp_path / "state.db"), FakeProvider(), sent.append, "active", {7}
    )
    packet = observation()
    packet.update(autonomous=True, party=None, mode="active")
    packet["bot"].update(objective="hunt", objective_running=True, potions=40)
    packet["actions"] += [
        {"id": key, "action": action, "description": key, "ttl_ms": 5000}
        for key, action in [
            ("hold", "hold"),
            ("retreat", "retreat"),
            ("hunt:1", "hunt"),
            ("hunt:2", "hunt"),
        ]
    ]
    snapshot = Observation.model_validate(packet)
    controller.latest[7] = snapshot
    controller.world = snapshot.world
    controller.supervisor.observe(snapshot)
    return controller, snapshot, sent, clock


def accepted(controller, action_id, candidate="hold", status="accepted"):
    controller._outcome(
        Outcome(
            world="world-a",
            bot_id=7,
            action_id=action_id,
            status=status,
            reason=candidate,
        )
    )


def test_recovery_waits_for_hold_ack_and_new_generation_before_another_action(
    tmp_path, monkeypatch
):
    c, snapshot, sent, clock = console(tmp_path, monkeypatch)
    active = c._apply(snapshot, "hunt:1")
    accepted(c, active, "hunt:1")
    c.supervisor.command(7, "recover", {})
    hold = sent[-1]
    assert hold["candidate_id"] == "hold"
    assert c.supervisor.blocked(7).keys() == {"hunt:1"}
    c.supervisor.observe(snapshot)
    assert sent[-1] == hold
    accepted(c, hold["action_id"])
    holding = snapshot.model_copy(
        update={
            "objective_generation": 3,
            "bot": snapshot.bot.model_copy(update={"objective": "hold"}),
        }
    )
    c.latest[7] = holding
    clock[0] += 1
    c.supervisor.observe(holding)
    assert sent[-1]["candidate_id"] == "hunt:2"
    assert sent[-1]["objective_generation"] == 3
    assert sent[-1]["lease"] == snapshot.lease
    assert c.supervisor.state(7)["phase"] == "waiting_action"
    accepted(c, sent[-1]["action_id"], "hunt:2")
    assert c.supervisor.state(7)["phase"] == "idle"
    assert (
        c.store.records("policy") == []
    )  # Advice/cancellation cannot fabricate rewards.


def test_pause_blocks_background_actions_and_renews_native_hold(tmp_path, monkeypatch):
    c, snapshot, sent, clock = console(tmp_path, monkeypatch)
    c.supervisor.command(7, "pause", {})
    accepted(c, sent[-1]["action_id"])
    assert c.supervisor.managed(7)
    assert c._apply(snapshot, "hunt:2") is None
    holding = snapshot.model_copy(
        update={
            "objective_generation": 3,
            "bot": snapshot.bot.model_copy(update={"objective": "hold"}),
        }
    )
    c.latest[7] = holding
    clock[0] += 21
    c.supervisor.observe(holding)
    assert [x["candidate_id"] for x in sent] == ["hold", "hold"]
    assert c.supervisor.state(7)["paused"]


def test_stale_state_and_human_party_cannot_be_controlled(tmp_path, monkeypatch):
    c, _snapshot, sent, clock = console(tmp_path, monkeypatch)
    clock[0] += 4
    with pytest.raises(ValueError, match="antiga"):
        c.supervisor.command(7, "recover", {})
    c.supervisor.received[7] = clock[0]
    party_snapshot = Observation.model_validate(observation())
    c.latest[7] = party_snapshot
    with pytest.raises(ValueError, match="party"):
        c.supervisor.command(7, "pause", {})
    assert not sent


def test_automatic_recovery_requires_five_minutes_and_does_not_interrupt_combat(
    tmp_path, monkeypatch
):
    c, snapshot, sent, clock = console(tmp_path, monkeypatch)
    for _ in range(59):
        clock[0] += 5
        c.supervisor.observe(snapshot)
    assert not sent
    clock[0] += 5
    combat = snapshot.model_copy(update={"nearby": [{"id": 123}]})
    c.supervisor.observe(combat)
    assert not sent
    assert any(row["kind"] == "stall" for _, row in c.store.records("operator_event"))
    # A quiet stall gets one safe recovery, never a teleport or native admin command.
    c.supervisor.state(7)["last_alert"] = 0
    c.supervisor.observe(snapshot)
    assert sent[-1]["candidate_id"] == "hold"
    assert {x["type"] for x in sent} == {"intent"}


def test_real_movement_and_xp_reset_stall_timer_but_counter_reset_does_not(
    tmp_path, monkeypatch
):
    c, snapshot, sent, clock = console(tmp_path, monkeypatch)
    for index in range(70):
        clock[0] += 5
        snapshot = snapshot.model_copy(
            update={"bot": snapshot.bot.model_copy(update={"xp": 1000 + index})}
        )
        c.supervisor.observe(snapshot)
    assert not sent
    assert c.supervisor.view()["bots"][0]["no_progress_seconds"] == 0


def test_retreat_stall_is_detected_even_when_combat_grants_xp(tmp_path, monkeypatch):
    c, snapshot, sent, clock = console(tmp_path, monkeypatch)
    for index in range(61):
        clock[0] += 5
        snapshot = snapshot.model_copy(
            update={
                "nearby": [{"id": 123}],
                "bot": snapshot.bot.model_copy(
                    update={
                        "objective": "retreat",
                        "xp": 1000 + index,
                    }
                ),
            }
        )
        c.latest[7] = snapshot
        c.supervisor.observe(snapshot)
    assert any(
        row["kind"] == "retreat_stall" for _, row in c.store.records("operator_event")
    )
    assert c.supervisor.view()["bots"][0]["diagnosis"] == "retreat_stalled"
    assert [item["candidate_id"] for item in sent] == ["retreat"]
    accepted(c, sent[-1]["action_id"], "retreat")
    for index in range(800):
        clock[0] += 5
        snapshot = snapshot.model_copy(
            update={
                "bot": snapshot.bot.model_copy(
                    update={
                        "position": [100 + index % 2, 100, 7],
                        "xp": 2000 + index,
                    }
                )
            }
        )
        c.latest[7] = snapshot
        c.supervisor.observe(snapshot)
        if len(sent) == 2 and c.supervisor.state(7)["phase"] == "waiting_action":
            accepted(c, sent[-1]["action_id"], "retreat")
    assert [item["candidate_id"] for item in sent] == ["retreat", "retreat"]
    for index in range(62):
        clock[0] += 5
        snapshot = snapshot.model_copy(
            update={
                "bot": snapshot.bot.model_copy(
                    update={
                        "position": [110, 100, 7],
                        "xp": 5000 + index,
                    }
                )
            }
        )
        c.latest[7] = snapshot
        c.supervisor.observe(snapshot)
    assert [item["candidate_id"] for item in sent] == ["retreat", "retreat", "retreat"]


def test_retreat_navigation_progress_and_observation_gaps_reset_timer(
    tmp_path, monkeypatch
):
    c, snapshot, sent, clock = console(tmp_path, monkeypatch)
    snapshot = snapshot.model_copy(
        update={"bot": snapshot.bot.model_copy(update={"objective": "retreat"})}
    )
    for index in range(130):
        clock[0] += 5
        if index == 59:
            snapshot = snapshot.model_copy(
                update={
                    "bot": snapshot.bot.model_copy(update={"position": [104, 100, 7]})
                }
            )
        if index == 118:
            clock[0] += 11
        c.latest[7] = snapshot
        c.supervisor.observe(snapshot)
    assert not sent
    assert not any(
        row["kind"] == "retreat_stall" for _, row in c.store.records("operator_event")
    )


def test_retreat_stall_survives_brief_objective_renewal_and_respects_pause(
    tmp_path, monkeypatch
):
    c, snapshot, sent, clock = console(tmp_path, monkeypatch)
    for index in range(62):
        clock[0] += 5
        goal = "follow" if 30 <= index < 36 else "retreat"
        snapshot = snapshot.model_copy(
            update={
                "bot": snapshot.bot.model_copy(
                    update={"objective": goal, "xp": index + 1000}
                )
            }
        )
        c.latest[7] = snapshot
        c.supervisor.observe(snapshot)
    assert [item["candidate_id"] for item in sent] == ["retreat"]

    (tmp_path / "other").mkdir()
    c2, snapshot, sent, clock = console(tmp_path / "other", monkeypatch)
    c2.supervisor.state(7)["paused"] = True
    c2.supervisor.state(7)["phase"] = "failed"
    for _ in range(62):
        clock[0] += 5
        snapshot = snapshot.model_copy(
            update={"bot": snapshot.bot.model_copy(update={"objective": "retreat"})}
        )
        c2.latest[7] = snapshot
        c2.supervisor.observe(snapshot)
    assert not sent


def test_retreat_stall_does_not_retry_when_automatic_is_disabled(tmp_path, monkeypatch):
    c, snapshot, sent, clock = console(tmp_path, monkeypatch)
    c.supervisor.state(7)["automatic"] = False
    for _ in range(62):
        clock[0] += 5
        snapshot = snapshot.model_copy(
            update={"bot": snapshot.bot.model_copy(update={"objective": "retreat"})}
        )
        c.latest[7] = snapshot
        c.supervisor.observe(snapshot)
    assert not sent
    assert any(
        row["kind"] == "retreat_stall" for _, row in c.store.records("operator_event")
    )


def test_advice_and_route_restriction_persist_and_can_be_removed(tmp_path, monkeypatch):
    c, snapshot, sent, clock = console(tmp_path, monkeypatch)
    key = c.supervisor.command(7, "note", {"text": "Evitar corredores sem saída."})[
        "id"
    ]
    c.supervisor.avoid(7, "hunt:1", 1800, "Operador")
    restored = Controller(c.store, FakeProvider(), sent.append, "active")
    assert restored.supervisor.advice(7)[0]["kind"] == "operator_advice"
    assert "hunt:1" not in {x.id for x in restored.supervisor.offers(snapshot).actions}
    assert restored._apply(snapshot, "hunt:1") is None
    clock[0] += 1801
    assert not restored.supervisor.blocked(7)
    c.supervisor.received[7] = clock[0]
    c.supervisor.command(7, "forget_note", {"id": key})
    assert not c.supervisor.advice(7)


async def test_readonly_chat_cannot_execute_even_if_model_proposes_action(
    tmp_path, monkeypatch
):
    c, _snapshot, sent, _clock = console(tmp_path, monkeypatch)

    class Model(FakeProvider):
        async def converse(self, snapshot, text, authorized, memory, deep):
            assert not authorized
            assert any(x.get("kind") == "operator_advice" for x in memory)
            return Proposal("hunt:1", "Proposta apenas.", "low")

    c.model = Model()
    c.supervisor.command(7, "note", {"text": "Preservar suprimentos."})
    result = await c.supervisor.chat(7, "Como está a caça?", False)
    assert result["status"] == "conversation_only"
    assert not sent


async def test_slow_chat_cannot_override_newer_operator_pause(tmp_path, monkeypatch):
    c, _snapshot, sent, _clock = console(tmp_path, monkeypatch)
    ready = asyncio.Event()

    class Model(FakeProvider):
        async def converse(self, *args, **kwargs):
            await ready.wait()
            return Proposal("hunt:2", "Vou propor outra rota.", "low")

    c.model = Model()
    task = asyncio.create_task(c.supervisor.chat(7, "Mude a caça", True))
    await asyncio.sleep(0)
    c.supervisor.command(7, "pause", {})
    ready.set()
    result = await task
    assert result["action_id"] is None
    assert [x["candidate_id"] for x in sent] == ["hold"]


async def test_chat_order_uses_fresh_offer_and_brief_hold_can_be_resumed(
    tmp_path, monkeypatch
):
    c, snapshot, sent, _clock = console(tmp_path, monkeypatch)
    result = await c.supervisor.chat(7, "Fique aqui", True)
    assert result["status"] == "requested"
    assert sent[-1]["candidate_id"] == "hold"
    accepted(c, result["action_id"])
    holding = snapshot.model_copy(
        update={
            "objective_generation": 3,
            "bot": snapshot.bot.model_copy(update={"objective": "hold"}),
        }
    )
    c.latest[7] = holding
    c.supervisor.observe(holding)
    c.supervisor.command(7, "resume", {})
    c.supervisor.observe(holding)
    assert sent[-1]["candidate_id"] in {"hunt:1", "hunt:2"}


def test_unacknowledged_recovery_stops_instead_of_looping(tmp_path, monkeypatch):
    c, snapshot, sent, clock = console(tmp_path, monkeypatch)
    c.supervisor.command(7, "recover", {})
    clock[0] += 13
    c.supervisor.observe(snapshot)
    assert c.supervisor.state(7)["phase"] == "failed"
    assert c.supervisor.state(7)["paused"]
    assert len(sent) == 1


def test_query_acknowledgements_do_not_duplicate_timeline(tmp_path, monkeypatch):
    c, _snapshot, sent, _clock = console(tmp_path, monkeypatch)
    c.supervisor.command(7, "pause", {})
    for _ in range(5):
        accepted(c, sent[-1]["action_id"])
    outcomes = [
        row for _, row in c.store.records("operator_event") if row["kind"] == "outcome"
    ]
    assert len(outcomes) == 1


def test_native_failed_hunt_is_not_retried_and_success_is_not_invented(
    tmp_path, monkeypatch
):
    c, snapshot, _sent, _clock = console(tmp_path, monkeypatch)
    action = c._apply(snapshot, "hunt:1")
    c._outcome(
        Outcome(
            world=snapshot.world,
            bot_id=7,
            action_id=action,
            status="failed",
            reason="no_confirmed_combat_progress",
            metrics={"elapsed_seconds": 300.0, "xp_delta": 0.0, "defeats_delta": 0.0},
        )
    )
    assert "hunt:1" in c.supervisor.blocked(7)
    assert c.store.get("episode", action)["status"] == "failed"
    assert c.supervisor.command(7, "resume", {})["status"] == "already_running"


def test_local_pause_and_route_exclusions_do_not_override_human_party(
    tmp_path, monkeypatch
):
    c, snapshot, _sent, _clock = console(tmp_path, monkeypatch)
    c.supervisor.command(7, "pause", {})
    c.supervisor.avoid(7, "hunt:1", 1800, "Operator")
    packet = snapshot.model_dump()
    packet["party"] = {"leader_id": 9, "members": [9, 7], "status": []}
    party = Observation.model_validate(packet)
    assert "hunt:1" in {item.id for item in c.supervisor.offers(party).actions}
    assert c._apply(party, "hunt:1") is not None


async def test_http_console_rejects_cross_origin_and_arbitrary_commands(
    tmp_path, monkeypatch
):
    c, _snapshot, sent, _clock = console(tmp_path, monkeypatch)
    api = OperatorServer(c.supervisor, 0)
    await api.start("127.0.0.1")

    async def request(
        method,
        path,
        host=None,
        origin=None,
        token=None,
        body=None,
    ):
        host = host or f"localhost:{api.port}"
        origin = origin or f"http://localhost:{api.port}"
        reader, writer = await asyncio.open_connection("127.0.0.1", api.port)
        payload = json.dumps(body).encode() if body else b""
        headers = f"{method} {path} HTTP/1.1\r\nHost: {host}\r\nOrigin: {origin}\r\nContent-Type: application/json\r\nContent-Length: {len(payload)}\r\nX-Operator-Token: {token or ''}\r\n\r\n"
        writer.write(headers.encode() + payload)
        await writer.drain()
        data = await reader.read()
        writer.close()
        await writer.wait_closed()
        return data

    try:
        response = await request("GET", "/api/state")
        assert b"200 Response" in response and b"operator_advice" not in response
        assert b"OPENAI_API_KEY" not in response
        assert b"403 Response" in await request(
            "GET", "/api/state", host="attacker.example:8091"
        )
        body = {"bot": 7, "operation": "pause"}
        assert b"403 Response" in await request(
            "POST",
            "/api/command",
            token=api.token,
            origin="http://attacker.example",
            body=body,
        )
        assert b"403 Response" in await request("POST", "/api/command", body=body)
        assert b"409 Response" in await request(
            "POST",
            "/api/command",
            token=api.token,
            body={"bot": 7, "operation": "teleport"},
        )
        assert b"200 Response" in await request(
            "POST", "/api/command", token=api.token, body=body
        )
        assert sent[-1]["candidate_id"] == "hold"
    finally:
        await api.close()


def _seed_hunt_stats(c, snapshot, candidate, mean, count):
    context = c.context(snapshot)
    c.store.put(
        "policy",
        f"7:{context}",
        {
            "version": "bandit-v1",
            "actions": {candidate: {"count": count, "mean": mean, "updated": 0.0}},
        },
    )
    return context


def _hunt_episode(c, snapshot, candidate, action_id, context):
    c.store.put(
        "episode",
        action_id,
        {
            "bot": 7,
            "world": snapshot.world,
            "context": context,
            "candidate": candidate,
            "selection": None,
            "started": 0.0,
            "status": "proposed",
            "terminal": False,
            "tool_call": None,
        },
    )


def _hunt_outcome(c, snapshot, action_id, status="completed"):
    c.supervisor.outcome(
        Outcome(
            world=snapshot.world,
            bot_id=7,
            action_id=action_id,
            status=status,
            reason="hunt_progress",
            metrics={"elapsed_seconds": 60.0, "xp_delta": 10.0, "defeats_delta": 1.0},
        )
    )


def test_reward_hiatus_excludes_a_sustainably_low_reward_hunt(tmp_path, monkeypatch):
    c, snapshot, _sent, _clock = console(tmp_path, monkeypatch)
    context = _seed_hunt_stats(c, snapshot, "hunt:1", mean=0.12, count=40)
    _hunt_episode(c, snapshot, "hunt:1", "act-1", context)
    _hunt_outcome(c, snapshot, "act-1")
    assert "hunt:1" in c.supervisor.blocked(7)
    offered = {a.id for a in c.supervisor.offers(snapshot).actions}
    assert "hunt:1" not in offered
    assert "hunt:2" in offered


def test_reward_hiatus_leaves_a_healthy_hunt_alone(tmp_path, monkeypatch):
    c, snapshot, _sent, _clock = console(tmp_path, monkeypatch)
    context = _seed_hunt_stats(c, snapshot, "hunt:1", mean=0.9, count=40)
    _hunt_episode(c, snapshot, "hunt:1", "act-1", context)
    _hunt_outcome(c, snapshot, "act-1")
    assert c.supervisor.blocked(7) == {}


def test_reward_hiatus_ignores_unsampled_hunts(tmp_path, monkeypatch):
    c, snapshot, _sent, _clock = console(tmp_path, monkeypatch)
    context = _seed_hunt_stats(c, snapshot, "hunt:1", mean=0.1, count=3)
    _hunt_episode(c, snapshot, "hunt:1", "act-1", context)
    _hunt_outcome(c, snapshot, "act-1")
    assert c.supervisor.blocked(7) == {}


def test_reward_hiatus_escalates_on_repeat_offense(tmp_path, monkeypatch):
    c, snapshot, _sent, clock = console(tmp_path, monkeypatch)
    context = _seed_hunt_stats(c, snapshot, "hunt:1", mean=0.12, count=40)
    _hunt_episode(c, snapshot, "hunt:1", "act-1", context)
    _hunt_outcome(c, snapshot, "act-1")
    first = c.supervisor.blocked(7)["hunt:1"]["until"] - clock[0]
    clock[0] += first + 1
    assert c.supervisor.blocked(7) == {}
    _hunt_episode(c, snapshot, "hunt:1", "act-2", context)
    _hunt_outcome(c, snapshot, "act-2")
    second = c.supervisor.blocked(7)["hunt:1"]["until"] - clock[0]
    assert second > first


def test_reward_hiatus_resets_when_a_hunt_recovers(tmp_path, monkeypatch):
    c, snapshot, _sent, clock = console(tmp_path, monkeypatch)
    context = _seed_hunt_stats(c, snapshot, "hunt:1", mean=0.12, count=40)
    _hunt_episode(c, snapshot, "hunt:1", "act-1", context)
    _hunt_outcome(c, snapshot, "act-1")
    assert c.supervisor.state(7)["reward_hiatus_offenses"]["hunt:1"] == 1
    _seed_hunt_stats(c, snapshot, "hunt:1", mean=0.8, count=50)
    clock[0] += 7201
    _hunt_episode(c, snapshot, "hunt:1", "act-2", context)
    _hunt_outcome(c, snapshot, "act-2")
    assert "hunt:1" not in c.supervisor.state(7).get("reward_hiatus_offenses", {})
    assert c.supervisor.blocked(7) == {}


def test_reward_hiatus_does_not_touch_party_companions(tmp_path, monkeypatch):
    c, snapshot, _sent, _clock = console(tmp_path, monkeypatch)
    party_snap = snapshot.model_copy(update={"autonomous": False})
    c.latest[7] = party_snap
    context = _seed_hunt_stats(c, party_snap, "hunt:1", mean=0.12, count=40)
    _hunt_episode(c, party_snap, "hunt:1", "act-1", context)
    _hunt_outcome(c, party_snap, "act-1")
    assert c.supervisor.blocked(7) == {}
