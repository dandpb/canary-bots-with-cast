#!/usr/bin/env python3
"""Offline technical party acceptance. Mutates only labelled private QA objects."""

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = Path("/tmp/canary-party-qa")
PREFIX = "canary-party-qa"
GAME = PREFIX + "-game"
DB = PREFIX + "-db"


def docker(*args, input=None, check=True):
    p = subprocess.run(
        ["docker", *map(str, args)],
        text=True,
        input=input,
        capture_output=True,
        check=False,
    )
    if check and p.returncode:
        raise RuntimeError(f"docker {args[:3]}: {p.stderr[-2500:]} {p.stdout[-1000:]}")
    return p.stdout.strip()


def verify():
    detail = json.loads(docker("inspect", GAME))[0]
    assert detail["Config"]["Labels"].get("canary.qa") == "party"
    assert set(detail["NetworkSettings"]["Networks"]) == {PREFIX}
    assert not detail["HostConfig"]["PortBindings"]
    assert detail["State"]["Running"], "private QA game stopped"


def command(script):
    verify()
    identifier = str(time.time_ns())
    raw = (
        "return {id="
        + json.dumps(identifier)
        + ",script="
        + json.dumps(script, ensure_ascii=False)
        + "}"
    )
    docker(
        "exec",
        "-i",
        GAME,
        "python3",
        "-c",
        "import os,sys;open('qa-command.tmp','w').write(sys.stdin.read());os.replace('qa-command.tmp','qa-command.lua')",
        input=raw,
    )
    for _ in range(120):
        raw = docker("exec", GAME, "cat", "/canary/qa-result.json", check=False)
        if raw:
            result = json.loads(raw)
            if result.get("id") == identifier:
                assert result["ok"], result
                return result.get("result")
        time.sleep(0.1)
    raise TimeoutError("private QA dispatcher did not respond")


def sql(query):
    detail = json.loads(docker("inspect", DB))[0]
    assert detail["Config"]["Labels"].get("canary.qa") == "party"
    assert set(detail["NetworkSettings"]["Networks"]) == {PREFIX}
    assert any(
        m.get("Name") == PREFIX + "-data" and m["Destination"] == "/var/lib/mysql"
        for m in detail["Mounts"]
    )
    return docker(
        "exec",
        DB,
        "mariadb",
        "-h127.0.0.1",
        "-ucanary",
        "-pparty-qa-only",
        "canary",
        "-N",
        "-e",
        query,
    )


def create():
    for name in [GAME, DB]:
        assert not docker("inspect", "--format", "{{.Name}}", name, check=False), (
            f"QA container already exists: {name}"
        )
    assert not docker(
        "network", "inspect", "--format", "{{.Name}}", PREFIX, check=False
    ), "retained QA network exists"
    assert not docker(
        "volume", "inspect", "--format", "{{.Name}}", PREFIX + "-data", check=False
    ), "retained QA database volume exists"
    WORK.mkdir(exist_ok=True)
    init = WORK / "initdb"
    init.mkdir(exist_ok=True)
    (init / "999_qa_background.sql").unlink(missing_ok=True)
    for index, rel in enumerate(
        [
            "schema.sql",
            "database/bots/00_bot_schema.sql",
            "database/bots/01_accounts.sql",
            "deployment/wsl/runtime-schema.sql",
        ]
    ):
        (init / f"{index:03}.sql").write_bytes((ROOT / rel).read_bytes())
    source = (ROOT / "database/bots/02_players.sql").read_bytes().decode("latin1")
    header = re.search(r"INSERT INTO `players` .*? VALUES ", source).group()
    rows = [
        re.search(r"\(" + str(guid) + r",.*?\)(?=[,;])", source).group()
        for guid in [65001, 65003, 65004]
    ]
    seed = header + ",".join(rows) + ";\n"
    seed += "UPDATE players SET town_id=1,posx=32369,posy=32241,posz=7,level=20,experience=98800,health=500,healthmax=500,mana=500,manamax=500,skill_sword=60,skill_axe=60,skill_club=60,skill_dist=60,maglevel=20,balance=100000 WHERE account_id=65000;\n"
    seed += "INSERT INTO accounts (id,name,password,email,type) VALUES (64999,'party-qa','offline-fixture','party@qa.invalid',1);\n"
    seed += "INSERT INTO accounts (id,name,password,email,type) VALUES (64998,'party-qa-b','offline-fixture','party-b@qa.invalid',1);\n"
    columns = re.search(r"INSERT INTO `players` (\(.*?\)) VALUES ", source).group(1)
    column_names = re.findall(r"`(.*?)`", columns)
    for guid, name in [(64999, "Party Leader A"), (64998, "Party Leader B")]:
        selected = ",".join(
            str(guid)
            if c in {"id", "account_id"}
            else repr(name)
            if c == "name"
            else "`" + c + "`"
            for c in column_names
        )
        seed += f"INSERT INTO players {columns} SELECT {selected} FROM players WHERE id=65001;\n"
    (init / "004_players.sql").write_bytes(seed.encode("latin1"))
    encoder = (ROOT / "tests/lua/bot_persistence_no_xp_test.lua").read_text()
    encoder = encoder[
        encoder.index("function qa.encode") : encoder.index("local function snapshot")
    ]
    adapter = (
        """assert(configManager.getString(configKeys.SERVER_NAME)=="Canary party QA")
BOT_CONFIG.MASTER_DISABLE=true
local qa={}
"""
        + encoder
        + """
PartyQA=assert(package.loadlib("/qa/party_acceptance.so","luaopen_party_acceptance"))()
local seen
local event=GlobalEvent("PartyAcceptanceQA")
function event.onThink()
 PartyQA("keepalive")
 local f=io.open("qa-command.lua","r"); if not f then return true end
 local raw=f:read("*a");f:close();local c=assert(loadstring(raw))()
 if seen==c.id then return true end;seen=c.id
 local loaded,failure=loadstring(c.script)
 local ok,result=false,failure
 if loaded then ok,result=pcall(loaded) end
 local out=assert(io.open("qa-result.tmp","w"));out:write(qa.encode({id=c.id,ok=ok,result=result}));out:close()
 os.rename("qa-result.tmp","qa-result.json");return true
end
event:interval(200);event:register()
"""
    )
    (WORK / "adapter.lua").write_text(adapter)
    (WORK / "brain.json").write_text(
        json.dumps(
            {
                "mode": "disabled",
                "bots": [65001, 65003, 65004],
                "socket_directory": "/run/party-brain",
            }
        )
    )
    entry = """import os
from pathlib import Path
Path('qa-command.lua').unlink(missing_ok=True)
config=Path('config.lua.dist').read_text()
config+='\\nmysqlHost="database"\\nmysqlUser="canary"\\nmysqlPass="party-qa-only"\\nmysqlDatabase="canary"\\nip="127.0.0.1"\\nserverName="Canary party QA"\\ndataPackDirectory="data-otservbr-global"\\nbotPlayersOnline=3\\nenableMetrics=false\\nhouseRentPeriod="never"\\nhouseLoseAfterInactivity=0\\nstartupDatabaseOptimization=false\\nbotAmbientRoamEnabled=false\\n'
Path('config.lua').write_text(config)
os.execv('/canary/canary',['/canary/canary'])
"""
    (WORK / "entry.py").write_text(entry)
    (WORK / "Dockerfile").write_text(
        "FROM canary-bots-wsl-game:local\nCOPY --chmod=0755 canary /canary/canary\nCOPY --chmod=0644 libbot_engine.so /canary/libbot_engine.so\n"
    )
    docker("build", "-t", "canary-party-qa:local", WORK)
    docker("network", "create", "--internal", "--label", "canary.qa=party", PREFIX)
    docker("volume", "create", "--label", "canary.qa=party", PREFIX + "-data")
    docker(
        "run",
        "-d",
        "--name",
        DB,
        "--label",
        "canary.qa=party",
        "--network",
        PREFIX,
        "--network-alias",
        "database",
        "-e",
        "MARIADB_ROOT_PASSWORD=party-qa-only",
        "-e",
        "MARIADB_DATABASE=canary",
        "-e",
        "MARIADB_USER=canary",
        "-e",
        "MARIADB_PASSWORD=party-qa-only",
        "-v",
        f"{PREFIX}-data:/var/lib/mysql",
        "-v",
        f"{init}:/docker-entrypoint-initdb.d:ro",
        "mariadb:11.4",
    )
    for _ in range(120):
        if (
            docker(
                "exec",
                DB,
                "mariadb",
                "-h127.0.0.1",
                "-ucanary",
                "-pparty-qa-only",
                "canary",
                "-N",
                "-e",
                "SELECT 1",
                check=False,
            )
            == "1"
        ):
            break
        time.sleep(1)
    else:
        raise TimeoutError("QA database authenticated TCP readiness")
    docker(
        "create",
        "--name",
        GAME,
        "--label",
        "canary.qa=party",
        "--network",
        PREFIX,
        "--network-alias",
        "game",
        "-v",
        f"{WORK}:/qa:ro",
        "-v",
        f"{ROOT}:/qa-repo:ro",
        "-v",
        "/tmp/canary-replay-deps:/qa-deps:ro",
        "-v",
        "/tmp/canary-lifecycle-qa-world.otbm:/canary/data-otservbr-global/world/otservbr.otbm:ro",
        "-v",
        f"{WORK}/adapter.lua:/canary/data/scripts/globalevents/aaa_party_qa.lua:ro",
        "-e",
        "CANARY_BRAIN_CONFIG=/qa/brain.json",
        "--entrypoint",
        "python3",
        "canary-party-qa:local",
        "/qa/entry.py",
    )
    docker("cp", str(ROOT / "data/scripts") + "/.", GAME + ":/canary/data/scripts/")
    docker(
        "cp",
        str(ROOT / "data/bot/authored") + "/.",
        GAME + ":/canary/data/bot/authored/",
    )
    docker("start", GAME)
    for _ in range(120):
        logs = docker("logs", "--tail", "15", GAME)
        if "canary party qa server online" in logs.lower():
            break
        time.sleep(1)
    print(
        json.dumps(
            {
                "stack": PREFIX,
                "database_readiness": "authenticated_tcp",
                "ports": [],
                "network_internal": True,
            }
        )
    )


def setup():
    return command("""Game.botCommand("_global","schedule off")
local names={"Grizzle Alyronia","Sever Heartspear","Galdon Whitehoof"}
for i,name in ipairs(names) do
 local p=Player(name) or assert(Game.loadBotPlayer(name));Game.botActivate(p:getGuid())
 Game.botSetAIPaused(p:getGuid(),true)
 local target=Position(32369+i,32241,7)
 if p:getPosition()~=target then assert(p:teleportTo(target)) end
 p:addItem(266,20);p:addItem(268,20)
end
PartyQA("town");PartyQA("login")
for i,name in ipairs({"Party Leader A","Party Leader B"}) do
 local p=Player(name);local target=Position(32368,32240+i,7)
 if p:getPosition()~=target then assert(p:teleportTo(target)) end
end
PartyQA("invite")
for _,name in ipairs(names) do Game.botSetAIPaused(Player(name):getGuid(),false) end
return PartyQA("inspect")""")


def stop():
    statuses = {}
    for name in [GAME, DB]:
        detail = json.loads(docker("inspect", name))[0]
        assert detail["Config"]["Labels"].get("canary.qa") == "party"
        assert set(detail["NetworkSettings"]["Networks"]) == {PREFIX}
        assert not detail["HostConfig"]["PortBindings"]
        if detail["State"]["Running"]:
            docker("stop", "-t", "30", name)
        after = json.loads(docker("inspect", name))[0]
        statuses[name] = {
            "running": after["State"]["Running"],
            "exit_code": after["State"]["ExitCode"],
            "qa_label": after["Config"]["Labels"].get("canary.qa"),
        }
    build = docker("inspect", "--format", "{{json .}}", PREFIX + "-build", check=False)
    if build:
        detail = json.loads(build)
        assert detail["Config"]["Labels"].get("canary.qa") == "party"
        state = detail["State"]
        statuses[PREFIX + "-build"] = {
            "running": state["Running"],
            "exit_code": state["ExitCode"],
            "qa_label": detail["Config"]["Labels"].get("canary.qa"),
        }
    (WORK / "teardown.json").write_text(json.dumps(statuses, indent=2) + "\n")
    assert all(not s["running"] and s["exit_code"] == 0 for s in statuses.values()), (
        statuses
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["create", "setup", "command", "sql", "stop"])
    p.add_argument("value", nargs="?")
    args = p.parse_args()
    if args.action == "create":
        create()
    elif args.action == "setup":
        print(setup())
    elif args.action == "command":
        print(json.dumps(command(args.value)))
    elif args.action == "sql":
        print(sql(args.value))
    elif args.action == "stop":
        stop()


if __name__ == "__main__":
    main()
