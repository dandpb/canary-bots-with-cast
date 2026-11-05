"""One-bot qualification. Only newly created private QA resources; no paid providers."""

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from canary_brain.benchmark import DockerFixture, Experiment, Participant, fixture_hash
from canary_brain.recording import digest

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(os.environ.get("CANARY_M5_QA", "/tmp/m5q-20261105a"))
WORLD = Path("/tmp/canary-lifecycle-qa-world.otbm")
IMAGE = "canary-m5-free-qa:20261105a"


def command(*args, timeout=300):
    value = subprocess.run(
        list(map(str, args)),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if value.returncode:
        raise RuntimeError(value.stderr[-2000:] + value.stdout[-1000:])
    return value.stdout.strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    WORK.mkdir(mode=0o700, exist_ok=False)
    fixture = WORK / "fixture"
    fixture.mkdir()
    seed = "\n".join(
        (ROOT / p).read_text()
        for p in [
            "schema.sql",
            "database/bots/00_bot_schema.sql",
            "deployment/wsl/runtime-schema.sql",
        ]
    )
    seed += "\nINSERT INTO accounts(id,name,password,email,type) VALUES(65000,'m5-offline','not-a-login-credential','m5@qa.invalid',1);\n"
    source = (ROOT / "database/bots/02_players.sql").read_bytes().decode("latin1")
    seed += re.search(r"INSERT INTO `players` .*? VALUES ", source).group()
    seed += re.search(r"\(65001,.*?\)(?=[,;])", source).group() + ";\n"
    seed += "UPDATE players SET vocation=4,level=20,experience=98800,health=365,healthmax=365,mana=95,manamax=95,cap=770,town_id=8,posx=32369,posy=32241,posz=7,skill_sword=50,skill_axe=50,skill_club=50,skill_shielding=50,maglevel=4,balance=10000 WHERE id=65001;\n"
    equipment = next(
        r
        for r in csv.DictReader((ROOT / "data/bot/authored/equipment.csv").open())
        if r["level"] == "20" and r["vocation"] == "4"
    )
    rows = []
    for slot, column in [
        (1, "slot_head"),
        (3, "slot_backpack"),
        (4, "slot_armor"),
        (5, "slot_right"),
        (6, "slot_left"),
        (7, "slot_legs"),
        (8, "slot_feet"),
    ]:
        rows.append(f"(65001,{slot},{100 + slot},{equipment[column]},1,'')")
    rows += ["(65001,103,201,266,20,'')", "(65001,103,202,268,20,'')"]
    seed += (
        "INSERT INTO player_items(player_id,pid,sid,itemtype,count,attributes) VALUES "
        + ",".join(rows)
        + ";\n"
    )
    (fixture / "database.sql").write_text(seed)
    (fixture / "character.json").write_text(
        json.dumps(
            {
                "id": 65001,
                "level": 20,
                "experience": 98800,
                "posx": 32369,
                "posy": 32241,
                "posz": 7,
            }
        )
    )
    shutil.copytree(ROOT / "data/bot/authored", fixture / "authored")
    hunts = fixture / "authored/hunt_scripts.csv"
    with hunts.open() as stream:
        reader = csv.DictReader(stream)
        fields, data = reader.fieldnames, list(reader)
    for row in data:
        row["enabled"] = "1" if row["id"] in {"77", "399"} else "0"
        if row["id"] == "77":
            row["vocation_mask"] = "8"
    with hunts.open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)
    build = WORK / "image"
    build.mkdir()
    shutil.copytree(ROOT / "data/scripts", build / "scripts")
    overrides = {
        "mysqlHost": "database",
        "mysqlUser": "canary",
        "mysqlDatabase": "canary",
        "ip": "127.0.0.1",
        "serverName": "Canary M5 free QA",
        "dataPackDirectory": "data-otservbr-global",
        "botPlayersOnline": 1,
        "enableMetrics": False,
        "houseRentPeriod": "never",
        "houseLoseAfterInactivity": 0,
        "startupDatabaseOptimization": False,
        "botPersonalityRerollOnRestart": False,
        "botAmbientRoamEnabled": False,
        "botActivityDwell": 0,
        "botActivityPoi": 0,
        "botActivityParty": 0,
        "botActivityTravel": 0,
        "botActivityHunt": 100,
        "botActivityRerollCooldownSec": 5,
        "botDwellPoiMinSec": 5,
        "botDwellPoiMaxSec": 5,
        "botDwellRerollMinSec": 5,
        "botDwellRerollMaxSec": 5,
        "botHuntTimeMinSec": 600,
        "botHuntTimeMaxSec": 600,
        "botResupplyRehuntPct": 100,
        "loginProtocolPort": 7171,
        "gameProtocolPort": 7172,
        "statusProtocolPort": 7173,
    }
    (build / "overrides.json").write_text(json.dumps(overrides))
    entry = "import json,os,shutil\nfrom pathlib import Path\nv=json.loads(Path('/m5-overrides.json').read_text());v['mysqlPass']=os.environ['MARIADB_PASSWORD']\nc=Path('config.lua.dist').read_text()+'\\n'+'\\n'.join(k+'='+json.dumps(x) for k,x in v.items())+'\\n'\nPath('config.lua').write_text(c)\nshutil.copyfile('/etc/canary-brain/server.json','data/bot/brain.json')\nos.execv('/canary/canary',['/canary/canary'])\n"
    (build / "entry.py").write_text(entry)
    encoder = (ROOT / "tests/lua/bot_persistence_no_xp_test.lua").read_text()
    encoder = encoder[
        encoder.index("function qa.encode") : encoder.index("local function snapshot")
    ]
    audit = (
        'assert(configManager.getString(configKeys.SERVER_NAME)=="Canary M5 free QA")\nBOT_CONFIG.MASTER_DISABLE=false\nBOT_CONFIG.SINGLE_BOT_NAME="Grizzle Alyronia"\nlocal qa={}\n'
        + encoder
    )
    audit += """
local event=GlobalEvent("M5FreeAudit")
function event.onThink()
 local p=Player("Grizzle Alyronia")
 if p then
  local pos=p:getPosition()
  local f=assert(io.open("/m5/character-live.jsonl","a"))
  f:write(qa.encode({at=Game.monotonicMs(),xp=p:getExperience(),hp=p:getHealth(),hpmax=p:getMaxHealth(),mana=p:getMana(),manamax=p:getMaxMana(),position={pos.x,pos.y,pos.z},potions=p:getItemCount(266)+p:getItemCount(268),bank=p:getBankBalance(),money=p:getMoney(),level=p:getLevel()}).."\\n");f:close()
 end
 return true
end
event:interval(1000);event:register()
"""
    (build / "scripts/globalevents/aaa_m5_free_qa.lua").write_text(audit)
    (build / "Dockerfile").write_text(
        'FROM canary-party-qa:local\nCOPY scripts/ /canary/data/scripts/\nRUN mv /canary/data/scripts/globalevents/bot_market_funding.lua /canary/qa-disabled-market-funding.lua && mv /canary/data/scripts/globalevents/bot_market.lua /canary/qa-disabled-market.lua\nCOPY entry.py /m5-entry.py\nCOPY overrides.json /m5-overrides.json\nENTRYPOINT ["python3","/m5-entry.py"]\n'
    )
    command("docker", "build", "-t", IMAGE, build)
    manifest = {
        "source_revision": command("git", "-C", ROOT, "rev-parse", "HEAD"),
        "fixture_sha256": fixture_hash(fixture, WORLD),
        "world_sha256": sha(WORLD),
        "world_bytes": WORLD.stat().st_size,
        "image_id": command("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"),
        "native_base": "33c6a57878e58ef1241d287d26bd5aa489b5cc50",
        "equipment": equipment,
        "guid": 65001,
        "hp": 365,
        "mana": 95,
        "level": 20,
        "xp": 98800,
        "bank": 10000,
        "potions": {266: 20, 268: 20},
        "overrides": overrides,
        "hunts": [77, 399],
        "hunt77_vocation_mask": 8,
        "files": {
            str(p.relative_to(fixture)): sha(p)
            for p in fixture.rglob("*")
            if p.is_file()
        },
        "binary_sha256": {
            n: sha(Path("/tmp/canary-party-qa") / n)
            for n in ["canary", "libbot_engine.so"]
        },
        "harness_sha256": {
            n: sha(ROOT / "tests/fixture" / n)
            for n in ["m5_qa.py", "m5_worker.py", "m5_stop.py"]
        },
    }
    (WORK / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in ["fixture_sha256", "image_id", "guid", "hp", "mana"]
            }
        )
    )


def run(mode):
    assert mode in {"native", "fake"}
    manifest = json.loads((WORK / "manifest.json").read_text())
    assert fixture_hash(WORK / "fixture", WORLD) == manifest["fixture_sha256"]
    directory = WORK / mode
    experiment = Experiment(
        name="m5-free",
        output=WORK / "attempts",
        fixture=WORK / "fixture",
        world_map=WORLD,
        budget_file=WORK / "unused-offline-ledger.sqlite3",
        game_image=manifest["image_id"],
        bot_id=65001,
        participants=[Participant(name="native", kind="native")],
        repetitions=1,
        seconds=1800,
        source_revision=manifest["source_revision"],
        expected_initial_sha256=manifest["fixture_sha256"],
    )
    harness = DockerFixture(
        experiment,
        directory,
        hashlib.sha256((WORK.name + ":" + mode).encode()).hexdigest(),
    )
    harness.prepare(Participant(name="native", kind="native"))
    server = directory / "config/server.json"
    value = json.loads(server.read_text())
    value["mode"] = "shadow" if mode == "native" else "active"
    server.write_text(json.dumps(value))
    compose = json.loads(harness.compose.read_text())
    compose["networks"] = {"default": {"internal": True}}
    compose["services"]["game"]["volumes"].append(f"{directory}:/m5")
    harness.compose.write_text(json.dumps(compose))
    config = {
        "provider": mode,
        "mode": value["mode"],
        "socket_directory": str(directory / "socket"),
        "state_file": str(directory / "worker.sqlite3"),
        "bots": [65001],
        "memory_mode": "frozen",
        "policy_seed": 42,
        "recording": {
            "path": str(directory / "recording.sqlite3"),
            "namespace": "m5-free-" + mode,
            "sample_ms": 1000,
        },
    }
    config["recording"]["manifests"] = [
        {
            "run_id": WORK.name + ":" + mode,
            "bot_id": 65001,
            "lineage": WORK.name,
            "experiment": "m5-free-qualification",
            "scenario": "thais-controlled-hunts",
            "participant": mode,
            "provider": mode,
            "model": "none",
            "memory_mode": "frozen",
            "initial_sha256": manifest["fixture_sha256"],
            "source_revision": manifest["source_revision"],
            "configuration_sha256": digest(
                {
                    "image_id": manifest["image_id"],
                    "initial": manifest["fixture_sha256"],
                    "overrides": manifest["overrides"],
                    "worker": manifest["harness_sha256"],
                    "mode": mode,
                }
            ),
        }
    ]
    (directory / "worker.json").write_text(json.dumps(config))
    worker = None
    result = {
        "mode": mode,
        "fixture_sha256": manifest["fixture_sha256"],
        "project": harness.project,
        "phase": "provisioning",
    }
    try:
        harness.start_database()
        result["initial_character"] = harness.character()
        assert result["initial_character"] == json.loads(
            (WORK / "fixture/character.json").read_text()
        )
        log = (directory / "worker.log").open("w")
        worker = subprocess.Popen(
            [
                "/tmp/canary-replay-venv/bin/python",
                str(ROOT / "tests/fixture/m5_worker.py"),
                str(directory),
                mode,
            ],
            env={**os.environ, "PYTHONPATH": str(ROOT / "deployment/brain/src")},
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        for _ in range(100):
            if (directory / "socket/worker.sock").exists():
                break
            if worker.poll() is not None:
                raise RuntimeError("offline worker startup failed")
            time.sleep(0.1)
        harness.start_game()
        result["phase"] = "observing"
        (directory / "result.json").write_text(json.dumps(result, indent=2))
        code = worker.wait(timeout=2100)
        assert code == 0, "offline worker failed; inspect private log"
        result["stop"] = json.loads((directory / "stop.json").read_text())
        harness.stop_game()
        result["saved_character"] = harness.character()
        result["phase"] = "finished"
    finally:
        if worker and worker.poll() is None:
            worker.terminate()
            worker.wait(timeout=30)
        harness.close()
        (directory / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "native", "fake"])
    args = parser.parse_args()
    prepare() if args.action == "prepare" else run(args.action)
