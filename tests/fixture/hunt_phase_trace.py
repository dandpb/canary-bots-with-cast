"""Read-only diagnostic for QA hunt phase logs; never an acceptance input."""

import re

from m5_qualification_gates import HUNT_PHASE, native_phase_cycle


TRACE = re.compile(
    r"\[HUNT:PHASE\] mono_ms=(\d+) bot_guid=(\d+) script_id=(\d+) "
    r"from=(PREPARING|TRAVEL_TO|PATROLLING|LEAVING|RESUPPLYING) "
    r"to=(PREPARING|TRAVEL_TO|PATROLLING|LEAVING|RESUPPLYING)(?:\s|$)"
)


def diagnose(log_lines, statuses, *, bot_guid, script_id, bot_name):
    """Compare two scoped observations; neither proves full transition coverage."""
    transitions = []
    for line in log_lines:
        match = TRACE.search(line)
        if not match:
            continue
        mono_ms, event_bot, event_script = map(int, match.group(1, 2, 3))
        if event_bot == bot_guid and event_script == script_id:
            transitions.append(
                {"mono_ms": mono_ms, "from": match.group(4), "to": match.group(5)}
            )

    observed_links_match = len(transitions) >= 2 and all(
        previous["mono_ms"] <= current["mono_ms"]
        and previous["to"] == current["from"]
        for previous, current in zip(transitions, transitions[1:])
    )
    # The historical status text names a bot and script, but has no GUID or hunt
    # instance. A matching phase sequence alone can span two separate hunts.
    prefix = f"Bot '{bot_name}':"
    scoped_statuses = []
    for row in statuses:
        value = row.get("status", "")
        parsed = HUNT_PHASE.search(value)
        if value.startswith(prefix) and parsed and int(parsed.group(1)) == script_id:
            scoped_statuses.append(row)

    sequence_observed = native_phase_cycle(scoped_statuses)["complete"]
    # Only enriched observations with the same GUID and explicit hunt instance
    # can make a same-hunt claim. The standard #92 rows lack those fields.
    instances = [row.get("hunt_instance_id") for row in scoped_statuses]
    same_hunt_proven = (
        sequence_observed
        and bool(instances)
        and all(row.get("bot_guid") == bot_guid for row in scoped_statuses)
        and all(isinstance(instance, (str, int)) and instance != "" for instance in instances)
        and len(set(instances)) == 1
    )
    return {
        "transitions": transitions,
        "trace_observed_links_match": observed_links_match,
        "trace_coverage": "partial",
        "status_scope": {"bot_name": bot_name, "script_id": script_id},
        "status_phase_sequence_observed": sequence_observed,
        "status_same_hunt_proven": same_hunt_proven,
        "status_hunt_cycle_proven": bool(same_hunt_proven),
    }
