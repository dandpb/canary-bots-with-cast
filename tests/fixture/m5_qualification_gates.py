"""Pure acceptance checks for a timed native/fake run, never an NPC purchase proof."""

import math
import re

HUMAN_OPERATIONS = {
    "pause",
    "resume",
    "recover",
    "retreat",
    "avoid",
    "note",
    "allow_route",
    "chat_act",
}
HUNT_PHASE = re.compile(r"hunt=\[script=(\d+).*?\bphase=([A-Z_]+)\b")


def ordered_events(events):
    """Preserve recorder order for events sharing a millisecond."""
    return [
        event
        for _, event in sorted(
            enumerate(events), key=lambda pair: (pair[1]["t_ms"], pair[0])
        )
    ]


def human_intervention(event):
    data = event.get("data", {})
    return (
        event.get("kind") == "operator"
        and data.get("operation") in HUMAN_OPERATIONS
        and not data.get("automatic", False)
    )


def native_phase_cycle(statuses):
    """Follow one hunt out to resupply, then observe hunting resume afterward."""
    matched = []
    expected = ("PATROLLING", "LEAVING", "RESUPPLYING", "PATROLLING")
    for _, row in sorted(
        enumerate(statuses), key=lambda pair: (pair[1]["elapsed"], pair[0])
    ):
        parsed = HUNT_PHASE.search(row.get("status", ""))
        if not parsed:
            continue
        script, phase = parsed.groups()
        if matched and len(matched) < 3 and script != matched[0]["hunt_id"]:
            matched = []
        if phase == expected[len(matched)]:
            matched.append(
                {
                    "elapsed": row["elapsed"],
                    "hunt_id": script,
                    "phase": phase,
                    "command_id": row.get("command_id"),
                }
            )
            if len(matched) == len(expected):
                return {
                    "complete": True,
                    "transitions": matched,
                    "meaning": "hunt phases only; does not establish an NPC purchase",
                }
        elif phase == "PATROLLING" and len(matched) < 3:
            matched = [
                {
                    "elapsed": row["elapsed"],
                    "hunt_id": script,
                    "phase": phase,
                    "command_id": row.get("command_id"),
                }
            ]
    return {
        "complete": False,
        "transitions": matched,
        "meaning": "hunt phases only; does not establish an NPC purchase",
    }


def action_identity(data):
    identity = data.get("action_id"), data.get("bot_id"), data.get("world")
    return (
        identity
        if isinstance(identity[0], str)
        and identity[0]
        and isinstance(identity[1], int)
        and isinstance(identity[2], str)
        and identity[2]
        else None
    )


def fake_hunt_restart(events):
    """Require a natural positive hunt completion followed by a new accepted hunt."""
    intents = {}
    completions = []
    for index, event in enumerate(ordered_events(events)):
        data = event.get("data", {})
        key = action_identity(data)
        if human_intervention(event):
            intents.clear()
            completions.clear()
            continue
        if event["kind"] == "intent" and key:
            if data.get("operator"):
                # An automatic recovery is reported separately; it cannot bridge
                # a failed natural episode into this successful restart proof.
                intents = {k: v for k, v in intents.items() if k[1:] != key[1:]}
                completions = [
                    row for row in completions if row["identity"][1:] != key[1:]
                ]
                continue
            if (
                data.get("operator") is not False
                or data.get("mode") != "active"
                or not re.fullmatch(r"hunt:\d+", data.get("candidate_id", ""))
            ):
                continue
            if key not in intents:
                intents[key] = {
                    "identity": key,
                    "candidate_id": data["candidate_id"],
                    "intent_t_ms": event["t_ms"],
                    "intent_index": index,
                    "stage": "intent",
                }
            continue
        if event["kind"] != "outcome" or key not in intents:
            continue
        entry = intents[key]
        status = data.get("status")
        if (
            status == "accepted"
            and data.get("reason") == "objective_started"
            and entry["stage"] == "intent"
        ):
            entry.update(stage="accepted", accepted_t_ms=event["t_ms"])
            previous = next(
                (
                    row
                    for row in completions
                    if row["identity"][1:] == key[1:]
                    and row["identity"] != key
                    and row["completed_index"] < entry["intent_index"]
                ),
                None,
            )
            if previous:
                return {
                    "complete": True,
                    "completed_hunt": public_action(previous),
                    "restart": public_action(entry),
                    "meaning": "completed hunt macro followed by a new accepted hunt; not return or NPC purchase",
                }
        elif status in {"completed", "failed", "cancelled"}:
            progress = data.get("metrics", {})
            if (
                status == "completed"
                and data.get("reason") == "hunt_progress"
                and entry["stage"] == "accepted"
                and progress.get("xp_delta", 0) > 0
                and progress.get("defeats_delta", 0) > 0
            ):
                entry.update(
                    stage="completed",
                    completed_t_ms=event["t_ms"],
                    completed_index=index,
                    xp_delta=progress["xp_delta"],
                    defeats_delta=progress["defeats_delta"],
                )
                completions.append(entry.copy())
            else:
                entry["stage"] = "terminal_without_progress"
    return {
        "complete": False,
        "meaning": "completed hunt macro followed by a new accepted hunt; not return or NPC purchase",
    }


def public_action(entry):
    return {
        key: value
        for key, value in entry.items()
        if key not in {"intent_index", "completed_index", "stage"}
    }


def simultaneous_hunts(events):
    for event in ordered_events(events):
        if event["kind"] != "sample":
            continue
        choices = sorted(
            {
                action["id"]
                for action in event["data"].get("actions", [])
                if action.get("action") == "hunt"
            }
        )
        if len(choices) >= 2:
            return {
                "offered": True,
                "t_ms": event["t_ms"],
                "candidate_ids": choices,
                "meaning": "simultaneous native offers; does not assert every offer reached a model",
            }
    return {"offered": False}


def in_horizon(value, seconds):
    return (
        isinstance(value, (int, float))
        and math.isfinite(value)
        and seconds <= value <= seconds + 5
    )


def terminal_stop(stops):
    """Accept one legacy terminal or the current matching finalize/seal pair."""
    if (
        len(stops) == 1
        and stops[0].get("reason") != "native_finalizing"
        and ("after_flush" not in stops[0] or stops[0]["after_flush"] is True)
    ):
        return stops[0]
    if len(stops) == 2:
        preparing, sealed = stops
        if (
            preparing.get("reason") == "native_finalizing"
            and preparing.get("after_flush") is not True
            and sealed.get("after_flush") is True
            and sealed.get("reason") != "native_finalizing"
            and all(
                preparing.get(field) == sealed.get(field)
                for field in ("elapsed_seconds", "observed_seconds")
            )
        ):
            return sealed
    return {}


def qualify_run(
    *,
    mode,
    run,
    events,
    metrics,
    initial,
    saved,
    requests,
    statuses=(),
    seconds=1800,
    require_progress=True,
):
    """Return scoped checks/evidence; image, cleanup and purchase attestations are external."""
    if mode not in {"native", "fake"}:
        raise ValueError("qualification supports native/fake only")
    require_progress = require_progress or seconds >= 1800
    events = ordered_events(events)
    samples = [event for event in events if event["kind"] == "sample"]
    stops = [
        event["data"]
        for event in events
        if event["kind"] == "lifecycle"
        and event["data"].get("phase") == "run_supervisor_stop"
    ]
    first = samples[0] if samples else None
    last = samples[-1] if samples else None
    span = (last["t_ms"] - first["t_ms"]) / 1000 if len(samples) >= 2 else None
    terminal = terminal_stop(stops)
    final_xp = last["data"]["bot"].get("xp") if last else None
    first_xp = first["data"]["bot"].get("xp") if first else None
    observed_xp_delta = (
        final_xp - first_xp if type(first_xp) is int and type(final_xp) is int else None
    )
    initial_xp = initial.get("experience")
    saved_xp = saved.get("experience")
    checks = {
        "completed": run.get("status") == "completed"
        and run.get("incomplete") is False,
        "supervisor_completed": bool(terminal)
        and terminal.get("reason") == "completed",
        "recorded_horizon": in_horizon(span, seconds),
        "observed_horizon": in_horizon(terminal.get("observed_seconds"), seconds),
        "elapsed_horizon": in_horizon(terminal.get("elapsed_seconds"), seconds),
        "no_gaps": metrics.get("gaps") == 0,
        "zero_observed_deaths": metrics.get("deaths") == 0
        and metrics.get("deaths_observed") is True,
        "no_operator_interventions": metrics.get("interventions") == 0
        and not any(human_intervention(event) for event in events),
        "zero_inference": requests == 0,
        "saved_xp_matches": final_xp is not None and saved_xp == final_xp,
    }
    window = [
        event
        for event in events
        if first and last and first["t_ms"] <= event["t_ms"] <= last["t_ms"]
    ]
    offers = simultaneous_hunts(window)
    cycle = (
        native_phase_cycle(
            [row for row in statuses if 0 <= row["elapsed"] <= seconds + 5]
        )
        if mode == "native"
        else fake_hunt_restart(window)
    )
    if require_progress:
        checks.update(
            {
                "positive_xp_observed": observed_xp_delta is not None
                and observed_xp_delta > 0
                and metrics.get("xp_delta") == observed_xp_delta,
                "positive_xp_persisted": isinstance(initial_xp, int)
                and isinstance(saved_xp, int)
                and saved_xp > initial_xp,
                "native_offers_multiple_hunts": offers["offered"],
                "hunt_cycle": cycle["complete"],
            }
        )
    return {
        "accepted": all(checks.values()),
        "checks": checks,
        "evidence": {
            "mode": mode,
            "span_seconds": span,
            "supervisor": stops,
            "initial_db_xp": initial_xp,
            "first_sample_xp": first_xp,
            "observed_xp_delta": observed_xp_delta,
            "saved_db_xp": saved_xp,
            "last_sample_xp": final_xp,
            "alternatives": offers,
            "hunt_cycle": cycle,
            "automatic_recoveries_requested": metrics.get(
                "automatic_recoveries_requested"
            ),
        },
        "scope": "timed gameplay only; runtime image/cleanup attestations and normal NPC purchase/return proof remain separate gates",
    }
