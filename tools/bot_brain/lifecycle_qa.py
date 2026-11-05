#!/usr/bin/env python3
"""Create/use a labelled, private disposable Canary lifecycle stack. No provider calls."""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "canary-lifecycle-qa"


def docker(*args, input=None, check=True):
    return subprocess.run(["docker", *map(str, args)], input=input, text=True,
                          capture_output=True, check=check).stdout.strip()


def verify(name):
    assert name.startswith(PREFIX)
    label = docker("inspect", "--format", '{{index .Config.Labels "canary.qa"}}', name)
    assert label == "lifecycle", "refusing to mutate an unlabelled container"


def command(action, **values):
    game = PREFIX + "-game"
    verify(game)
    identifier = time.time_ns()
    fields = {"id": str(identifier), "action": action, **values}
    assert all(isinstance(v, (str, int, bool)) for v in fields.values())
    data = "return {" + ",".join("[" + json.dumps(k) + "]=" + json.dumps(v, ensure_ascii=False)
                                  for k, v in fields.items()) + "}"
    docker("exec", "-i", game, "python3", "-c",
           "import os,sys;open('qa-command.tmp','w').write(sys.stdin.read());os.replace('qa-command.tmp','qa-command.lua')", input=data)
    if action == "shutdown":
        return {"requested": True} # Completion is verified with docker wait + fresh SQL.
    for _ in range(600):
        if _ % 10 == 0:
            assert docker("inspect", "--format", "{{.State.Running}}", game) == "true", "disposable QA game exited before responding"
        result = docker("exec", game, "cat", "/canary/qa-result.json", check=False)
        if result:
            value = json.loads(result)
            if value.get("id") == str(identifier):
                assert value.get("ok"), value
                return value["result"]
        time.sleep(0.1)
    raise TimeoutError("QA command did not finish")


def create(world, build):
    assert build.startswith(("canary-state-qa", "canary-reload-a")), "QA build container required"
    work = Path("/tmp") / PREFIX
    work.mkdir(exist_ok=True)
    init = work / "initdb"
    init.mkdir(exist_ok=True)
    (init / "000_schema.sql").write_text((ROOT / "schema.sql").read_text())
    for i, source in enumerate(["database/bots/00_bot_schema.sql", "database/bots/01_accounts.sql",
                                "deployment/wsl/runtime-schema.sql"], 1):
        (init / f"{i:03}.sql").write_text((ROOT / source).read_text())
    # mysqldump contains raw binary attributes in quoted literals.
    source = (ROOT / "database/bots/02_players.sql").read_bytes().decode("latin1")
    header = re.search(r"INSERT INTO `players` .*? VALUES ", source).group()
    rows = [re.search(r"\(" + str(guid) + r",.*?\)(?=[,;])", source).group() for guid in [65001, 65003, 65004]]
    (init / "004_players.sql").write_bytes((header + ",".join(rows) + ";\n" +
        "UPDATE players SET town_id=1,posx=32369,posy=32241,posz=7,level=8,experience=4200,skill_sword=10,skill_sword_tries=0,maglevel=1,manaspent=0 WHERE account_id=65000;\n").encode("latin1"))
    entry = '''import os
from pathlib import Path
config = Path("config.lua.dist").read_text()
Path("qa-command.lua").unlink(missing_ok=True)
config += '\\nmysqlHost="database"\\nmysqlUser="canary"\\nmysqlPass="lifecycle-qa-only"\\nmysqlDatabase="canary"\\nip="127.0.0.1"\\nserverName="Canary lifecycle QA"\\ndataPackDirectory="data-otservbr-global"\\nbotPlayersOnline=3\\nenableMetrics=false\\nhouseRentPeriod="never"\\nhouseLoseAfterInactivity=0\\nstartupDatabaseOptimization=false\\n'
Path("config.lua").write_text(config)
os.execv("/canary/canary", ["/canary/canary"])
'''
    (work / "entry.py").write_text(entry)
    adapter = '''local qa = dofile("/qa-repo/tests/lua/bot_persistence_no_xp_test.lua")
local event = GlobalEvent("CanaryLifecycleQA")
local seen
function event.onThink()
 local file = io.open("qa-command.lua", "r")
 if not file then return true end
 local raw = file:read("*a"); file:close()
 local command = assert(loadstring(raw))()
 if command.id == seen then return true end
 seen = command.id
 local ok, result = pcall(qa.run, command)
 local out = assert(io.open("qa-result.tmp", "w"))
 out:write(qa.encode({id=command.id,ok=ok,result=result})); out:close()
 os.rename("qa-result.tmp", "qa-result.json")
 return true
end
event:interval(200)
event:register()
'''
    (work / "adapter.lua").write_text(adapter)
    docker("network", "create", "--internal", "--label", "canary.qa=lifecycle", PREFIX)
    database = PREFIX + "-db"
    docker("run", "-d", "--name", database, "--label", "canary.qa=lifecycle", "--network", PREFIX,
           "--network-alias", "database", "-e", "MARIADB_ROOT_PASSWORD=lifecycle-qa-only",
           "-e", "MARIADB_DATABASE=canary", "-e", "MARIADB_USER=canary", "-e", "MARIADB_PASSWORD=lifecycle-qa-only",
           "-v", f"{init}:/docker-entrypoint-initdb.d:ro", "mariadb:11.4")
    game = PREFIX + "-game"
    docker("create", "--name", game, "--label", "canary.qa=lifecycle", "--network", PREFIX,
           "-v", f"{world.resolve()}:/canary/data-otservbr-global/world/otservbr.otbm:ro",
           "-v", f"{work}:/qa:ro", "-v", f"{ROOT}:/qa-repo:ro",
           "-v", f"{work / 'adapter.lua'}:/canary/data/scripts/globalevents/aaa_lifecycle_qa.lua:ro",
           "--entrypoint", "python3", "canary-bots-wsl-game:local", "/qa/entry.py")
    for artifact in ["canary", "libbot_engine.so"]:
        docker("cp", f"{build}:/build/bin/{artifact}", work / artifact)
        docker("cp", work / artifact, f"{game}:/canary/{artifact}")
    # Current Lua helpers are paired with the new native API.
    docker("cp", ROOT / "data/scripts/lib/bot_system.lua", f"{game}:/canary/data/scripts/lib/bot_system.lua")
    for _ in range(120):
        if docker("exec", database, "healthcheck.sh", "--connect", "--innodb_initialized", check=False) == "":
            state = docker("exec", database, "mariadb", "-uroot", "-plifecycle-qa-only", "-N", "-e", "SELECT 1", check=False)
            if state == "1": break
        time.sleep(1)
    else: raise TimeoutError("disposable database did not initialize")
    docker("start", game)
    print(json.dumps({"game": game, "database": database, "network": PREFIX, "work": str(work)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--world", type=Path)
    parser.add_argument("--build", default="canary-state-qa-build")
    parser.add_argument("--action")
    parser.add_argument("--values", default="{}")
    args = parser.parse_args()
    if args.create:
        assert args.world and args.world.is_file()
        create(args.world, args.build)
    elif args.action:
        print(json.dumps(command(args.action, **json.loads(args.values))))
