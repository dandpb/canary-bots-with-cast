"""Grounded intent probability routing, clarification prompts, and factual outcome summaries."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from .protocol import Candidate

_DEFERRED_CUES = ("quando", "depois", "se ", "mais tarde", "assim que")


def route_probability(
    probability: float,
    *,
    act_threshold: float = 0.70,
    reject_threshold: float = 0.30,
) -> Literal["act", "clarify", "abstain"]:
    """Route a calibrated decision probability into act, clarify, or abstain."""
    if not (
        math.isfinite(reject_threshold)
        and math.isfinite(act_threshold)
        and 0.0 <= reject_threshold < act_threshold <= 1.0
    ):
        raise ValueError("thresholds must satisfy 0.0 <= reject_threshold < act_threshold <= 1.0")
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be within [0.0, 1.0]")
    if probability >= act_threshold:
        return "act"
    if probability <= reject_threshold:
        return "abstain"
    return "clarify"


def _candidate_label(item: Candidate) -> str:
    prefix = "Guide a prudent party hunt: "
    desc = item.description.strip()
    if desc.startswith(prefix):
        desc = desc[len(prefix) :].strip()
    return f"{item.id} ({desc})" if desc else item.id


def clarification_question(
    message: str,
    offered_actions: Sequence[Candidate],
    *,
    candidate_id: str | None = None,
) -> str:
    """Return a single grounded Portuguese clarifying question from offered candidates."""
    lowered = message.casefold()
    if any(cue in lowered for cue in _DEFERRED_CUES):
        return "Quer que eu faça isso agora ou só depois da atividade atual?"

    by_id = {item.id: item for item in offered_actions}
    if candidate_id is not None and candidate_id != "continue" and candidate_id in by_id:
        return f"Você quer confirmar agora a ação {_candidate_label(by_id[candidate_id])}?"

    hunts = [item for item in offered_actions if item.action == "hunt"]
    if len(hunts) >= 2:
        options = "; ".join(_candidate_label(item) for item in hunts[:3])
        return f"Qual destas hunts elegíveis você prefere agora: {options}?"

    actionable = [item for item in offered_actions if item.action != "continue"]
    if actionable:
        options = "; ".join(_candidate_label(item) for item in actionable[:3])
        return f"Qual destas ações disponíveis você quer iniciar agora: {options}?"

    return "Não há nenhuma ação elegível agora além de continuar; quer aguardar ou mudar de posição?"


def confirm_action_reply(offered_actions: Sequence[Candidate], candidate_id: str) -> str:
    """Return a concise grounded confirmation reply proposing an offered action."""
    by_id = {item.id: item for item in offered_actions}
    item = by_id.get(candidate_id)
    label = _candidate_label(item) if item is not None else candidate_id
    return f"Entendido, vou propor agora: {label}."[:600]


def _int_metric(metrics: Mapping[str, Any] | None, key: str) -> int | None:
    if not metrics or key not in metrics:
        return None
    raw = metrics[key]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
        return None
    return round(raw)


def format_factual_outcome(
    candidate: str,
    status: str,
    reason: str,
    metrics: Mapping[str, Any] | None = None,
) -> str:
    """Summarize an observed server outcome strictly from authoritative fields."""
    supply_delta = _int_metric(metrics, "supply_delta")
    defeats_delta = _int_metric(metrics, "defeats_delta")
    xp_delta = _int_metric(metrics, "xp_delta")

    if status in {"accepted", "running"}:
        return f"{candidate}: aceito pelo servidor ({status}); ainda em andamento, sem conclusão confirmada."

    if reason == "supplies_bought_and_party_rejoined":
        extra = f" (saldo de poções: {supply_delta:+d})" if supply_delta is not None else ""
        return f"{candidate}: compra concluída com retorno à party{extra}."

    if reason == "supplies_bought":
        extra = f" (saldo de poções: {supply_delta:+d})" if supply_delta is not None else ""
        return f"{candidate}: compra concluída em modo solo, sem retorno de party registrado{extra}."

    if reason == "return_route_unavailable":
        partial = (
            f" Saldo de poções observado: {supply_delta:+d}."
            if supply_delta is not None and supply_delta != 0
            else ""
        )
        return f"{candidate}: {status} (return_route_unavailable); o retorno não foi concluído.{partial}"

    if reason == "purchase_incomplete_or_insufficient_funds":
        return f"{candidate}: falhou ({reason}); compra incompleta ou saldo insuficiente."

    if reason == "hunt_progress" or candidate.startswith("hunt:"):
        parts: list[str] = []
        if defeats_delta is not None:
            parts.append(f"{defeats_delta} derrotas")
        if xp_delta is not None:
            parts.append(f"{xp_delta} XP")
        detail = f" com {' e '.join(parts)}" if parts else ""
        reason_note = f" ({reason})" if reason else ""
        return f"{candidate}: {status}{reason_note}{detail}, sem inventar loot."

    reason_note = f" ({reason})" if reason else ""
    return f"{candidate}: {status}{reason_note}."
