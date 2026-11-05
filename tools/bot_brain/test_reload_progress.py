#!/usr/bin/env python3
"""Reload TRAVELING/DWELLING through the labelled disposable server only."""
import json
import time

import lifecycle_qa as qa


def state(operation="inspect", **values):
    return qa.command("reloadProgress", operation=operation, **values)


def run():
    qa.verify(qa.PREFIX + "-game")
    qa.command("load")
    qa.command("huntFixture", text="stop")
    state("sourceTown")
    print(json.dumps(qa.command("huntFixture", text="hunt 1")), flush=True)
    before = state()
    print(json.dumps({"travel_before": before}), flush=True)
    assert before["state"] == 5 and before["pendingHuntAfterTravel"]
    assert "script 1 " in before["reservations"]
    assert qa.command("reload")["ok"]
    after = state()
    state("arrived")  # Arrival boundary only; no claim to simulate the boat journey.
    arrived = state("tick")  # Production engine tick / doTraveling / beginHuntPhase.
    travel = {"before": before, "after": after, "arrived": arrived}
    print(json.dumps({"travel": travel}), flush=True)
    phases = []
    for operation in ("preparing", "resupplying"):
        phase_before = state(operation)
        assert qa.command("reload")["ok"]
        phase_after = state()
        phase_tick = state("tick")
        phases.append((phase_before, phase_after, phase_tick))
        print(json.dumps({operation: {"before": phase_before, "after": phase_after, "tick": phase_tick}}), flush=True)
    qa.command("huntFixture", text="stop")

    before_dwell = state("dwelling", delay=5000)
    assert qa.command("reload")["ok"]
    after_dwell = state()
    early = state("tick")
    remaining = max(0, before_dwell["dwellUntil"] - early["now"])
    time.sleep(remaining / 1000 + .25)
    expired = state("tick")
    dwell = {"before": before_dwell, "after": after_dwell, "early": early, "expired": expired}
    print(json.dumps({"dwell": dwell}), flush=True)

    for name in ("Sever Heartspear", "Galdon Whitehoof"):
        qa.command("load", name=name)
    debug = qa.command("reloadDebug")
    print(json.dumps({"debug": debug}), flush=True)

    assert before["runtimeId"] == after["runtimeId"] == arrived["runtimeId"]
    assert after["pendingHuntAfterTravel"], "reload dropped pending cross-town hunt"
    assert arrived["state"] == 7 and arrived["huntPhase"] == 0, "arrival did not start PREPARING"
    assert not arrived["pendingHuntAfterTravel"] and arrived["huntId"] == 1
    assert "script 1 " in arrived["reservations"]
    for phase_before, phase_after, phase_tick in phases:
        for field in ("prepareStarted", "prepareWaitUntil", "prepareStep", "resupplyStarted", "resupplyPhase", "resupplyRerolled"):
            assert phase_after[field] == phase_before[field], (field, phase_before, phase_after)
        assert phase_tick["huntPhase"] == phase_before["huntPhase"] and phase_tick["prepareStep"] == 1, phase_tick
    assert before_dwell["runtimeId"] == after_dwell["runtimeId"]
    assert after_dwell["dwellUntil"] == before_dwell["dwellUntil"], "reload changed dwell deadline"
    assert early["state"] == 2, "DWELLING ended before its original deadline"
    assert expired["state"] == 1, "DWELLING did not end after its original deadline"
    assert not debug["outcome"]["ok"] and not debug["outcome"]["pending"]
    assert "Scheduler: ON" in debug["schedulerBefore"] and "Scheduler: ON" in debug["schedulerAfter"]
    identity = lambda rows: sorted((r["guid"], r["runtimeId"], r["active"], r["hibernated"]) for r in rows)
    assert identity(debug["before"]) == identity(debug["after"]), debug
    before_expired = state("dwelling", delay=-1000)
    assert qa.command("reload")["ok"]
    after_expired = state()
    assert after_expired["dwellUntil"] == before_expired["dwellUntil"]
    assert state("tick")["state"] == 1, "reload restarted an already expired dwell"
    qa.command("huntFixture", text="stop")
    state("unavailableHunt")
    assert qa.command("reload")["ok"]
    cancelled = state()
    print(json.dumps({"cancelled_unavailable_hunt": cancelled}), flush=True)
    assert (cancelled["state"], cancelled["huntId"], cancelled["pendingHuntAfterTravel"]) == (1, 0, False), cancelled
    assert "script 4294967294 " not in cancelled["reservations"], "cancelled hunt leaked a reservation"
    print("PASS travel reservation becomes PREPARING and original dwell deadline survives reload", flush=True)


if __name__ == "__main__":
    run()
