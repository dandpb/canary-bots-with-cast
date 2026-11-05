"""Reduce preserved native status/audit evidence without issuing game commands."""

import json
import re
import sys
from pathlib import Path


def report(work):
    work = Path(work)
    phases = []
    previous = None
    status_file = work / "phase-status.jsonl"
    for line in status_file.read_text().splitlines() if status_file.exists() else []:
        row = json.loads(line)
        status = row.get("status", "")
        match = re.search(
            r"script=(\d+).*?phase=(\w+).*?kills=(\d+).*?wp=(\d+)", status
        )
        state = re.search(r"state=(\w+)", status)
        current = (
            (state.group(1) if state else None, *match.groups()[:2])
            if match
            else (state.group(1) if state else None,)
        )
        if current != previous:
            phases.append({"elapsed": row["elapsed"], "status": status})
            previous = current
    audit = [
        json.loads(line)
        for line in (work / "character-live.jsonl").read_text().splitlines()
    ]
    return {
        "read_only_status_transitions": phases,
        "first_live_audit": audit[0],
        "last_live_audit": audit[-1],
        "audit_samples": len(audit),
        "bank_debit": audit[0]["bank"] - audit[-1]["bank"],
        "potions_gained": audit[-1]["potions"] - audit[0]["potions"],
        "limits": "Status starts after 540 observed seconds and samples every 10 seconds; unobserved transitions are not reconstructed. Hunt phase RESUPPLYING alone does not prove a purchase.",
    }


if __name__ == "__main__":
    print(json.dumps(report(sys.argv[1]), indent=2))
