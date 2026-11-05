#!/usr/bin/env python3
"""Shared quest and deterministic quest-role regression on labelled QA only."""

import json

import lifecycle_qa as qa

ACTORS = [(65001, "Grizzle Alyronia"), (65003, "Sever Heartspear")]


def state(guid, operation="inspect"):
    return qa.command("reloadProgress", guid=guid, operation=operation)


def run():
    qa.verify(qa.PREFIX + "-game")
    # Private QA config uses quest percentage 4: GUID suffixes 1/3 are quest
    # roles, suffix 4 is a regular role, covering both sides of the policy.
    qa.command("load", name="Galdon Whitehoof")
    qa.command("huntFixture", name="Galdon Whitehoof", text="stop")
    regular_role_before = state(65004)
    assert not regular_role_before["isQuestBot"], "QA config requires botQuestBotPct=4"
    before = []
    for guid, name in ACTORS:
        qa.command("load", name=name)
        qa.command("huntFixture", name=name, text="stop")
        state(guid, "sourceTown")
        selected = qa.command("huntFixture", name=name, text="hunt 38")
        print(json.dumps({"assignment": selected}), flush=True)
        before.append(state(guid, "questProgress"))
    assert all(s["huntId"] == 38 and s["isQuestBot"] for s in before), before
    assert qa.command("reload")["ok"]
    after = [state(guid) for guid, _ in ACTORS]
    regular_role_after = state(65004)
    print(json.dumps({"shared": {"before": before, "after": after}}), flush=True)
    print(
        json.dumps(
            {
                "role_control": {
                    "before": regular_role_before,
                    "after": regular_role_after,
                }
            }
        ),
        flush=True,
    )

    # QA config sets botResupplyRehuntPct=100. The production completion/reroll
    # path calls tryStartHunt; no forced quest ID is used for the next selection.
    state(65001, "questCompleted")
    next_quest = state(65001, "tick")
    print(json.dumps({"next_quest": next_quest}), flush=True)
    next_script = json.loads(
        qa.docker(
            "exec",
            qa.PREFIX + "-game",
            "python3",
            "-c",
            "import csv,json,sys;print(json.dumps(next(r for r in csv.DictReader(open('/canary/data/bot/authored/hunt_scripts.csv')) if int(r['id'])==int(sys.argv[1]))))",
            next_quest["huntId"],
        )
    )
    print(json.dumps({"next_script": next_script}), flush=True)

    # A conflicting ordinary hunt must still have one owner after reload.
    for guid, name in ACTORS:
        qa.command("huntFixture", name=name, text="stop")
        state(guid, "regularCollision")
    assert qa.command("reload")["ok"]
    ordinary = [state(guid) for guid, _ in ACTORS]
    print(json.dumps({"ordinary": ordinary}), flush=True)

    for old, restored in zip(before, after):
        for field in (
            "runtimeId",
            "huntId",
            "huntPhase",
            "waypoint",
            "kills",
            "isQuestBot",
        ):
            assert restored[field] == old[field], (field, old, restored)
        assert restored["state"] == 7, restored
        assert "script 38 " not in restored["reservations"], (
            "shared quest became exclusively reserved"
        )
    assert (
        not regular_role_after["isQuestBot"]
        and regular_role_after["runtimeId"] == regular_role_before["runtimeId"]
    )
    assert next_quest["isQuestBot"] and (
        next_script["is_quest"] == "1" or next_script["script_category"] == "quest"
    ), next_quest
    assert f"script {next_quest['huntId']} " not in next_quest["reservations"]
    assert sum(s["huntId"] == 1 and s["state"] == 7 for s in ordinary) == 1, ordinary
    assert sum(s["huntId"] == 0 and s["state"] == 1 for s in ordinary) == 1, ordinary
    print(
        "PASS shared quest progress/role/next selection and exclusive ordinary hunts survive reload",
        flush=True,
    )


if __name__ == "__main__":
    run()
