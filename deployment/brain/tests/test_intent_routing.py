"""Unit tests for intent probability routing, clarification prompts, and factual outcome summaries."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_protocol import observation

from canary_brain.controller import Controller
from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.intent_routing import (
    clarification_question,
    confirm_action_reply,
    format_factual_outcome,
    route_probability,
)
from canary_brain.protocol import Candidate, Observation
from canary_brain.provider import DialogueRoute, Prices, Proposal, Provider
from canary_brain.store import BudgetExceeded, Store
from tools import jev_experiments


def _cand(cid: str, action: str, desc: str = "Action description") -> Candidate:
    return Candidate(id=cid, action=action, description=desc, ttl_ms=5000)


def test_route_probability_bands_and_validation() -> None:
    assert route_probability(0.92) == "act"
    assert route_probability(0.70) == "act"
    assert route_probability(0.55) == "clarify"
    assert route_probability(0.31) == "clarify"
    assert route_probability(0.30) == "abstain"
    assert route_probability(0.05) == "abstain"

    with pytest.raises(ValueError):
        route_probability(-0.1)
    with pytest.raises(ValueError):
        route_probability(1.1)
    with pytest.raises(ValueError):
        route_probability(float("nan"))
    with pytest.raises(ValueError):
        route_probability(0.5, act_threshold=0.3, reject_threshold=0.7)


def test_clarification_question_stays_grounded_in_offered_actions() -> None:
    offered = [
        _cand("continue", "continue", "Continue the current useful objective"),
        _cand("hunt:7", "hunt", "Guide a prudent party hunt: Dark Cathedral -2 (lvl 60-180, dist 85, same floor)"),
        _cand("hunt:401", "hunt", "Guide a prudent party hunt: Venore East Coryms (lvl 60-240, dist 45, floor 7)"),
        _cand("resupply", "resupply", "Walk to the town shop to replenish supplies and return"),
    ]

    deferred = clarification_question("Cola em mim quando terminar a hunt", offered)
    assert "agora ou só depois" in deferred

    confirm = clarification_question("vai lá?", offered, candidate_id="resupply")
    assert "resupply" in confirm
    assert "hunt:999" not in confirm

    choose_hunt = clarification_question("bora caçar?", offered)
    assert "hunt:7" in choose_hunt and "hunt:401" in choose_hunt
    assert "hunt:999" not in choose_hunt

    single_action = clarification_question("faz algo", [offered[0], offered[3]])
    assert "resupply" in single_action

    empty_actionable = clarification_question("faz algo", [offered[0]])
    assert "além de continuar" in empty_actionable


def test_format_factual_outcome_distinguishes_status_and_reasons() -> None:
    accepted = format_factual_outcome("resupply", "accepted", "", {})
    assert "ainda em andamento" in accepted
    assert "concluída" not in accepted

    solo = format_factual_outcome("resupply", "completed", "supplies_bought", {"supply_delta": 17})
    assert "modo solo" in solo
    assert "sem retorno de party" in solo
    assert "+17" in solo

    party = format_factual_outcome(
        "resupply", "completed", "supplies_bought_and_party_rejoined", {"supply_delta": 38}
    )
    assert "retorno à party" in party
    assert "+38" in party

    partial_fail = format_factual_outcome(
        "resupply", "failed", "return_route_unavailable", {"supply_delta": 34}
    )
    assert "não foi concluído" in partial_fail
    assert "+34" in partial_fail

    funds = format_factual_outcome(
        "resupply", "failed", "purchase_incomplete_or_insufficient_funds", {"supply_delta": 0}
    )
    assert "compra incompleta ou saldo insuficiente" in funds

    hunt = format_factual_outcome(
        "hunt:7", "completed", "hunt_progress", {"defeats_delta": 12, "xp_delta": 900}
    )
    assert "12 derrotas" in hunt
    assert "900 XP" in hunt
    assert "sem inventar loot" in hunt


def test_jev_experiments_loads_slang_clarification_fixtures() -> None:
    fixtures_path = Path(__file__).resolve().parents[1] / "tools" / "jev_experiment_cases.json"
    data = json.loads(fixtures_path.read_text(encoding="utf-8"))
    slang = jev_experiments.intent_cases(data, "slang_clarification")
    all_cases = jev_experiments.intent_cases(data, "all")
    assert len(slang) == 8
    assert len(all_cases) == 40 + 20 + 8
    assert all(c.group == "slang_clarification" for c in slang)


def test_confirm_action_reply_is_grounded_and_provisional() -> None:
    offered = [
        _cand("continue", "continue", "Continue the current useful objective"),
        _cand(
            "hunt:7",
            "hunt",
            "Guide a prudent party hunt: Dark Cathedral -2 (lvl 60-180, dist 85, same floor)",
        ),
    ]
    reply = confirm_action_reply(offered, "hunt:7")
    assert "hunt:7" in reply
    assert "Dark Cathedral -2" in reply
    assert "propor" in reply
    assert confirm_action_reply(offered, "resupply").endswith("resupply.")


def _decisions_client(answers: list[dict[str, object]], *, model: str = "gpt-6-luna", deployment: str | None = None):
    calls: list[dict[str, object]] = []

    async def create(**kwargs):
        calls.append(kwargs)
        data = {
            "model": model,
            "answers": answers,
            "usage": {"input_tokens": 120, "output_tokens": 0},
        }
        return SimpleNamespace(model_dump=lambda **kw: data)

    async def raw_create(**kwargs):
        calls.append(kwargs)
        data = {
            "model": model,
            "answers": answers,
            "usage": {"input_tokens": 120, "output_tokens": 0},
        }
        return SimpleNamespace(
            headers={
                "x-litellm-model-id": deployment or "deployment-a",
                "x-litellm-call-id": "gateway-req-1",
            },
            parse=lambda: SimpleNamespace(model_dump=lambda **kw: data),
        )

    return SimpleNamespace(
        decisions=SimpleNamespace(
            create=create,
            with_raw_response=SimpleNamespace(create=raw_create),
        )
    ), calls


def _multi_hunt_observation() -> dict[str, object]:
    packet = observation()
    packet["actions"].extend(
        [
            {
                "id": "hunt:7",
                "action": "hunt",
                "description": "Guide a prudent party hunt: Dark Cathedral -2 (lvl 60-180, dist 85, same floor)",
                "ttl_ms": 5000,
            },
            {
                "id": "hunt:401",
                "action": "hunt",
                "description": "Guide a prudent party hunt: Venore East Coryms (lvl 60-240, dist 45, floor 7)",
                "ttl_ms": 5000,
            },
        ]
    )
    return packet


async def test_provider_route_dialogue_acts_on_confident_immediate_command(tmp_path) -> None:
    answers = [
        {"type": "predicate", "name": "plan", "probability": 0.04},
        {"type": "predicate", "name": "sequence", "probability": 0.03},
        {"type": "predicate", "name": "actionable", "probability": 0.92},
        {"type": "choice", "name": "action", "choice": "resupply", "confidence": 0.88},
    ]
    client, calls = _decisions_client(answers)
    provider = Provider(Store(tmp_path / "brain.db"), client)
    snap = Observation.model_validate(observation())

    route = await provider.route_dialogue(snap, "vai comprar potions agora", True)
    assert route is not None
    assert route.decision == "act"
    assert route.candidate_id == "resupply"
    assert route.probability == pytest.approx(0.88)
    assert "resupply" in route.reply
    assert len(calls) == 1
    q_names = [(q["type"], q["name"]) for q in calls[0]["questions"]]
    assert q_names == [
        ("predicate", "plan"),
        ("predicate", "sequence"),
        ("predicate", "actionable"),
        ("choice", "action"),
    ]


@pytest.mark.parametrize(
    ("p_actionable", "choice", "confidence", "expected_candidate", "expected_substr"),
    [
        (0.52, "resupply", 0.65, "resupply", "confirmar agora a ação resupply"),
        (0.85, "hunt:7", 0.42, None, "hunt:7"),
        (0.88, "continue", 0.90, None, "hunt:7"),
    ],
)
async def test_provider_route_dialogue_clarifies_ambiguous_or_low_confidence(
    tmp_path,
    p_actionable: float,
    choice: str,
    confidence: float,
    expected_candidate: str | None,
    expected_substr: str,
) -> None:
    answers = [
        {"type": "predicate", "name": "plan", "probability": 0.08},
        {"type": "predicate", "name": "sequence", "probability": 0.05},
        {"type": "predicate", "name": "actionable", "probability": p_actionable},
        {"type": "choice", "name": "action", "choice": choice, "confidence": confidence},
    ]
    client, _ = _decisions_client(answers)
    provider = Provider(Store(tmp_path / "brain.db"), client)
    snap = Observation.model_validate(_multi_hunt_observation())

    route = await provider.route_dialogue(snap, "bora lá", True)
    assert route is not None
    assert route.decision == "clarify"
    assert route.candidate_id == expected_candidate
    assert expected_substr in route.reply
    assert "hunt:999" not in route.reply


@pytest.mark.parametrize(
    ("p_plan", "p_sequence", "p_actionable"),
    [
        (0.80, 0.05, 0.40),
        (0.05, 0.75, 0.90),
        (0.10, 0.05, 0.15),
    ],
)
async def test_provider_route_dialogue_defers_to_converse_for_plan_sequence_or_abstain(
    tmp_path, p_plan: float, p_sequence: float, p_actionable: float
) -> None:
    answers = [
        {"type": "predicate", "name": "plan", "probability": p_plan},
        {"type": "predicate", "name": "sequence", "probability": p_sequence},
        {"type": "predicate", "name": "actionable", "probability": p_actionable},
        {"type": "choice", "name": "action", "choice": "resupply", "confidence": 0.80},
    ]
    client, _ = _decisions_client(answers)
    provider = Provider(Store(tmp_path / "brain.db"), client)
    snap = Observation.model_validate(observation())

    route = await provider.route_dialogue(snap, "como está seu hp?", True)
    assert route == DialogueRoute("converse", probability=p_actionable)


async def test_route_dialogue_bypasses_without_api_call_when_ineligible(tmp_path) -> None:
    answers = [
        {"type": "predicate", "name": "plan", "probability": 0.01},
        {"type": "predicate", "name": "sequence", "probability": 0.01},
        {"type": "predicate", "name": "actionable", "probability": 0.99},
        {"type": "choice", "name": "action", "choice": "resupply", "confidence": 0.99},
    ]
    client, calls = _decisions_client(answers, model="model-a", deployment="deployment-a")
    provider = Provider(Store(tmp_path / "brain.db"), client)
    snap = Observation.model_validate(observation())

    assert await provider.route_dialogue(snap, "reabastece", False) is None
    assert await provider.route_dialogue(snap, "reabasteça e depois espere", True) is None
    assert await provider.route_dialogue(snap, "monta uma estratégia", True) is None
    only_continue = snap.model_copy(update={"actions": [snap.actions[0]]})
    assert await provider.route_dialogue(only_continue, "reabastece", True) is None
    assert calls == []

    gw_responses = GatewayProvider(
        Store(tmp_path / "gw-resp.db"),
        client,
        gateway=GatewayConfiguration(
            alias="participant-a",
            effective_model="model-a",
            deployment_id="deployment-a",
            provider="test",
            version="pinned-test",
            configuration_sha256="a" * 64,
            decision_api="responses",
            prices=Prices(
                version="test",
                input_nanousd=1,
                cached_nanousd=1,
                cache_write_nanousd=1,
                output_nanousd=2,
            ),
        ),
    )
    assert await gw_responses.route_dialogue(snap, "reabastece", True) is None
    assert calls == []

    gw_decisions = GatewayProvider(
        Store(tmp_path / "gw-dec.db"),
        client,
        gateway=GatewayConfiguration(
            alias="participant-a",
            effective_model="model-a",
            deployment_id="deployment-a",
            provider="test",
            version="pinned-test",
            configuration_sha256="a" * 64,
            decision_api="decisions",
            decisions_output_nanousd=0,
            prices=Prices(
                version="test",
                input_nanousd=1,
                cached_nanousd=1,
                cache_write_nanousd=1,
                output_nanousd=2,
            ),
        ),
    )
    route = await gw_decisions.route_dialogue(
        snap, "reabastece agora", True, [{"speaker": "human", "text": "oi"}]
    )
    assert route is not None
    assert route.decision == "act"
    assert route.candidate_id == "resupply"
    assert len(calls) == 1
    part = calls[0]["input"][0]["content"][0]  # type: ignore[index]
    assert part["type"] == "input_text"
    projected = json.loads(part["text"])
    assert projected["message"] == "reabastece agora"
    assert projected["recent_dialogue"] == [{"speaker": "human", "text": "oi"}]


async def test_controller_dialogue_pre_router_act_clarify_and_fallback(tmp_path) -> None:
    class Model:
        def __init__(self, outcome: DialogueRoute | Exception):
            self.outcome = outcome
            self.converse_calls = 0
            self.route_calls = 0

        async def decide(self, *args, **kwargs):
            return "continue"

        async def route_dialogue(self, *args, **kwargs):
            self.route_calls += 1
            if isinstance(self.outcome, Exception):
                raise self.outcome
            return self.outcome

        async def converse(self, *args, **kwargs):
            self.converse_calls += 1
            return Proposal("resupply", "Fallback converse.", "low")

    # 1) "act" applies intent & saves memory without calling converse
    sent: list[dict[str, object]] = []
    store_act = Store(tmp_path / "act.db")
    model_act = Model(
        DialogueRoute("act", "resupply", 0.91, "Entendido, vou propor agora: resupply.")
    )
    ctrl_act = Controller(store_act, model_act, sent.append, mode="active")
    pkt = observation() | {
        "mode": "active",
        "messages": [{"id": "m-act", "player_id": 9, "text": "compra pots"}],
    }
    await ctrl_act.handle(pkt)
    await ctrl_act.drain()
    assert model_act.route_calls == 1
    assert model_act.converse_calls == 0
    assert any(p.get("type") == "reply" and "resupply" in str(p.get("text")) for p in sent)
    assert [p["candidate_id"] for p in sent if p.get("type") == "intent"] == ["resupply"]
    mem = store_act.get("memory", "7:9")
    assert mem is not None and mem["entries"][-1]["speaker"] == "bot"

    # 2) "clarify" replies & stores memory without calling converse or applying intent
    sent_clarify: list[dict[str, object]] = []
    store_clarify = Store(tmp_path / "clarify.db")
    model_clarify = Model(
        DialogueRoute("clarify", "resupply", 0.52, "Você quer confirmar agora a ação resupply?")
    )
    ctrl_clarify = Controller(store_clarify, model_clarify, sent_clarify.append, mode="active")
    pkt2 = observation() | {
        "mode": "active",
        "messages": [{"id": "m-clarify", "player_id": 9, "text": "vai lá"}],
    }
    await ctrl_clarify.handle(pkt2)
    await ctrl_clarify.drain()
    assert model_clarify.route_calls == 1
    assert model_clarify.converse_calls == 0
    assert any(p.get("type") == "reply" and "confirmar" in str(p.get("text")) for p in sent_clarify)
    assert not any(p.get("type") == "intent" for p in sent_clarify)
    assert store_clarify.get("memory", "7:9") is not None

    # 3) "converse" or transient error falls back to converse
    for outcome in (
        DialogueRoute("converse", probability=0.12),
        RuntimeError("transient decisions timeout"),
    ):
        sent_fb: list[dict[str, object]] = []
        model_fb = Model(outcome)
        ctrl_fb = Controller(Store(tmp_path / f"fb-{id(outcome)}.db"), model_fb, sent_fb.append, mode="active")
        pkt3 = observation() | {
            "mode": "active",
            "messages": [{"id": "m-fb", "player_id": 9, "text": "e aí, tudo certo?"}],
        }
        await ctrl_fb.handle(pkt3)
        await ctrl_fb.drain()
        assert model_fb.route_calls == 1
        assert model_fb.converse_calls == 1
        assert any(p.get("type") == "reply" and p.get("text") == "Fallback converse." for p in sent_fb)

    # 4) Leadership transfer during slow route_dialogue still blocks intent application
    ready = asyncio.Event()

    class SlowActModel:
        async def decide(self, *args, **kwargs):
            return "continue"

        async def route_dialogue(self, *args, **kwargs):
            await ready.wait()
            return DialogueRoute("act", "resupply", 0.95, "Vou propor resupply.")

        async def converse(self, *args, **kwargs):
            raise AssertionError("converse must not be called")

    sent_xfer: list[dict[str, object]] = []
    ctrl_xfer = Controller(Store(tmp_path / "xfer.db"), SlowActModel(), sent_xfer.append, mode="active")
    pkt_init = observation() | {
        "mode": "active",
        "messages": [{"id": "m-xfer", "player_id": 9, "text": "compra pots"}],
    }
    await ctrl_xfer.handle(pkt_init)
    await asyncio.sleep(0)
    pkt_changed = observation() | {"mode": "active", "objective_generation": 3}
    pkt_changed["party"]["leader_id"] = 10
    await ctrl_xfer.handle(pkt_changed)
    ready.set()
    await ctrl_xfer.drain()
    assert not any(p.get("type") == "intent" for p in sent_xfer)

    # 5) BudgetExceeded in route_dialogue sends unavailable reply and stops cleanly
    sent_budget: list[dict[str, object]] = []
    model_budget = Model(BudgetExceeded("monthly cap reached"))
    ctrl_budget = Controller(Store(tmp_path / "budget.db"), model_budget, sent_budget.append, mode="active")
    pkt_budget = observation() | {
        "mode": "active",
        "messages": [{"id": "m-budget", "player_id": 9, "text": "compra pots"}],
    }
    await ctrl_budget.handle(pkt_budget)
    await ctrl_budget.drain()
    assert model_budget.converse_calls == 0
    assert any(p.get("type") == "reply" and "indisponível" in str(p.get("text")) for p in sent_budget)
    assert not any(p.get("type") == "intent" for p in sent_budget)
