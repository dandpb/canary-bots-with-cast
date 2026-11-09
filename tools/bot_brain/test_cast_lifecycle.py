#!/usr/bin/env python3
"""Real Player/protocol/SQL/HTTP cast lifecycle in the private labelled QA stack.

Requires its matching lifecycle_bridge.so and a web container on the QA network,
configured only for the disposable database. No external sockets are published.
"""
import json
import time

import lifecycle_qa as qa

NAME = "Lifecycle Human"
GAME = qa.PREFIX + "-game"


def sql(statement):
    database = qa.PREFIX + "-db"
    qa.verify(database)
    return qa.docker("exec", database, "mariadb", "-uroot", "-plifecycle-qa-only",
                     "-N", "canary", "-e", statement)


def cast(operation):
    return qa.command("cast", operation=operation)


def listed():
    qa.verify(qa.PREFIX + "-web")
    return json.loads(qa.docker("exec", GAME, "python3", "-c", """
import json,urllib.request
request=urllib.request.Request('http://web/login.php',
 data=json.dumps({'type':'login','accountname':'@cast','password':''}).encode(),
 headers={'Content-Type':'application/json'})
payload=json.load(urllib.request.urlopen(request,timeout=5))
print(json.dumps([c['name'] for c in payload['playdata']['characters']]))
"""))


def wait_listed(expected):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if (NAME in listed()) == expected:
            return
        time.sleep(.1)
    raise AssertionError((expected, listed()))


def run():
    qa.verify(GAME)
    qa.seed_human()
    cast("human")
    cast("on")
    wait_listed(True)
    assert cast("view")["viewers"] == 1
    cast("replace")
    late = cast("lateRelease")
    assert late["broadcasting"] and late["viewers"] == 1, late
    closed = cast("release")
    assert not closed["broadcasting"] and closed["viewers"] == 0, closed
    wait_listed(False)
    print("PASS real protocol release/late release, viewers and HTTP publication", flush=True)

    cast("human")
    cast("on")
    wait_listed(True)
    cast("drop")  # Real Connection::close posts ProtocolGame::release.
    wait_listed(False)
    assert not cast("status")["broadcasting"]
    print("PASS connection loss closes viewers and withdraws HTTP publication", flush=True)

    cast("human")
    cast("on")
    wait_listed(True)
    sql("CREATE TRIGGER qa_delay_cast BEFORE DELETE ON cast_broadcasters "
        "FOR EACH ROW DO SLEEP(2)")
    try:
        cast("off")
        start = time.monotonic()
        qa.command("dbprobe")
        probe_ms = (time.monotonic() - start) * 1000
        assert probe_ms < 1000, probe_ms
        cast("on")
        time.sleep(2.5)
        wait_listed(True)
        assert sql("SELECT COUNT(*) FROM cast_broadcasters WHERE player_id=64999") == "1"
        print(f"PASS delayed DELETE/new start and dispatcher probe {probe_ms:.0f}ms", flush=True)
    finally:
        sql("DROP TRIGGER IF EXISTS qa_delay_cast")

    sql("CREATE TRIGGER qa_reject_cast BEFORE DELETE ON cast_broadcasters "
        "FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='isolated cast failure'")
    try:
        cast("off")
        time.sleep(4)  # Beyond three immediate attempts and multiple backoff retries.
        assert NAME in listed()
    finally:
        sql("DROP TRIGGER IF EXISTS qa_reject_cast")
    wait_listed(False)
    print("PASS failed deletion remains recoverable beyond immediate retry limit", flush=True)

    cast("on")
    wait_listed(True)
    cast("logout")
    wait_listed(False)
    print("PASS normal logout removes HTTP publication", flush=True)
    cast("human")
    cast("on")
    wait_listed(True)
    qa.command("death")
    wait_listed(False)
    print("PASS actual human death removes HTTP publication", flush=True)

    qa.command("load")
    before = cast("botState")
    qa.command("hibernate")
    assert cast("botState")["hibernated"]
    deadline = time.monotonic() + 5
    while "Grizzle Alyronia" not in listed():
        assert time.monotonic() < deadline, "hibernated bot missing from HTTP casts"
        time.sleep(.1)
    assert "Grizzle Alyronia".encode().hex() in cast("list")
    cast("watchBot")
    after = cast("botState")
    assert not after["hibernated"] and after["viewers"] == 1, after
    assert before["runtimeId"] == after["runtimeId"], (before, after)
    print("PASS hibernated bot listed in HTTP/TCP and same Player awakened by viewer", flush=True)


if __name__ == "__main__":
    run()
