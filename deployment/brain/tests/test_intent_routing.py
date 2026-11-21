"""Unit tests for intent probability routing, clarification prompts, and factual outcome summaries."""

import json
from pathlib import Path

import pytest

from canary_brain.intent_routing import (
    clarification_question,
    format_factual_outcome,
    route_probability,
)
from canary_brain.protocol import Candidate
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
