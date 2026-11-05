#!/usr/bin/env python3
"""Live #12 regression against the labelled disposable lifecycle stack only.

Requires the matching test-only lifecycle_bridge.so. --fault-library optionally
injects a QA build whose loadHuntData throws after successful preparation.
"""
import argparse
import json
import time
from pathlib import Path

import lifecycle_qa as qa

GAME = qa.PREFIX + "-game"
DATABASE = qa.PREFIX + "-db"


def sql(statement):
    qa.verify(DATABASE)
    return qa.docker("exec", DATABASE, "mariadb", "-uroot", "-plifecycle-qa-only",
                     "-N", "canary", "-e", statement)


def identity():
    return sorted((e["guid"], e["runtimeId"], e["active"], e["hibernated"])
                  for e in qa.command("roster"))


def resources():
    return json.loads(qa.docker("exec", GAME, "python3", "-c", """
import json
from pathlib import Path
print(json.dumps({
    'modules':len({l.split()[-1] for l in Path('/proc/1/maps').read_text().splitlines()
                   if 'libbot_engine.so.reload-' in l}),
    'snapshots':len(list(Path('/canary').glob('libbot_engine.so.reload-*'))),
    'fds':len(list(Path('/proc/1/fd').iterdir()))}))
"""))


def run(swaps, fault):
    qa.verify(GAME)
    for name in ("Grizzle Alyronia", "Sever Heartspear", "Galdon Whitehoof"):
        # Re-runs wake an already pooled character before loading it.
        roster = {e["guid"]: e for e in qa.command("roster")}
        guid = {"Grizzle Alyronia": 65001, "Sever Heartspear": 65003, "Galdon Whitehoof": 65004}[name]
        if roster.get(guid, {}).get("hibernated"):
            qa.command("wake", name=name)
        qa.command("load", name=name)
    before = qa.command("counts")
    qa.command("arm", delay=1800)
    qa.command("unregister")
    time.sleep(2)
    after = qa.command("counts")
    assert (after["fired"], after["destroyed"]) == (before["fired"], before["destroyed"] + 1)
    qa.command("load")  # Re-register the same world-owned Player, without a DB load.
    qa.command("mutate", value=901, charges=2)
    qa.command("mutate", name="Sever Heartspear", value=902, charges=4)
    qa.command("hibernate", name="Sever Heartspear")
    original = identity()
    qa.command("arm", delay=3000)
    assert qa.command("reload")["ok"]
    assert identity() == original
    time.sleep(3.2)
    counts = qa.command("counts")
    assert (counts["fired"], counts["destroyed"]) == (after["fired"], after["destroyed"] + 1)
    print("PASS same Players, hibernation and callback cancellation", flush=True)

    qa.docker("exec", GAME, "mv", "libbot_engine.so", "libbot_engine.qa-backup.so")
    try:
        assert not qa.command("reload")["ok"]
        assert identity() == original
    finally:
        qa.docker("exec", GAME, "mv", "libbot_engine.qa-backup.so", "libbot_engine.so")
    print("PASS missing candidate leaves active engine and roster intact", flush=True)

    if fault:
        assert fault.is_file()
        qa.docker("exec", GAME, "cp", "libbot_engine.so", "libbot_engine.qa-backup.so")
        qa.docker("cp", fault, GAME + ":/canary/libbot_engine.qa-next.so")
        sql("CREATE TRIGGER qa_reject_save BEFORE UPDATE ON players FOR EACH ROW "
            "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='isolated reload save failure'")
        try:
            qa.command("mutate", value=903, charges=5)
            qa.docker("exec", GAME, "mv", "libbot_engine.qa-next.so", "libbot_engine.so")
            failed = qa.command("reload")
            assert not failed["ok"] and "isolated init failure" in failed["message"], failed
            qa.docker("exec", GAME, "mv", "libbot_engine.qa-backup.so", "libbot_engine.so")
            assert qa.command("reload")["ok"]
            assert identity() == original
            state = qa.command("inspect")
            assert (state["storage"], state["charges"], state["xp"]) == (903, 5, 4200), state
            print("PASS post-commit failure/retry retains unsaved Players with SQL unavailable", flush=True)
        finally:
            sql("DROP TRIGGER IF EXISTS qa_reject_save")
            qa.docker("exec", GAME, "sh", "-c",
                      "if test -f libbot_engine.qa-backup.so; then "
                      "mv libbot_engine.qa-backup.so libbot_engine.so; fi")
        qa.command("save")

    start = resources()
    for i in range(swaps):
        assert qa.command("reload")["ok"]
        assert identity() == original
        if (i + 1) % 10 == 0:
            print(f"reload {i + 1}: {resources()}", flush=True)
    end = resources()
    assert start["modules"] == end["modules"] == end["snapshots"] == 1, (start, end)
    assert end["fds"] <= start["fds"] + 2, (start, end)
    state = qa.command("wake", name="Sever Heartspear")
    assert (state["storage"], state["charges"], state["xp"]) == (902, 4, 4200), state
    print(f"PASS {swaps} real reloads: {start} -> {end}; pooled inventory retained", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swaps", type=int, default=50)
    parser.add_argument("--fault-library", type=Path)
    args = parser.parse_args()
    assert args.swaps > 0
    run(args.swaps, args.fault_library)
