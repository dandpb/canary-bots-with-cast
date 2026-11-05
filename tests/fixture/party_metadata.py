"""Capture source/artifact identity and offline ledger checks from the private QA game."""

import hashlib
import json
import os
import platform
from pathlib import Path

import party_qa as q

NATIVE_BASE = "33c6a57878e58ef1241d287d26bd5aa489b5cc50"
# Scenario definitions pinned to the tested native base, not latest upstream data.
DATA_BLOBS = {
    "data-otservbr-global/npc/xodet.lua": "7f0fa10d9047093037465b06c56ba6f394fbc7db",
    "data/XML/vocations.xml": "050f30faecbaa1c6b95f7e50d2ebc2dbdc6bd952",
    "data/items/items.xml": "7e973c4ddd5049d3ccc02ed4cacbe50d66537443",
    "data-otservbr-global/monster/mammals/wolf.lua": "2b1a13734e9ef49cb0ca689fffc368ec7453a848",
}


def main():
    q.verify()
    environment = {
        "native_base": NATIVE_BASE,
        "architecture": platform.machine(),
        "kernel": platform.release(),
        "logical_cpus": os.cpu_count(),
        "runtime_artifacts": {
            name: hashlib.sha256((q.WORK / name).read_bytes()).hexdigest()
            for name in ["canary", "libbot_engine.so", "party_acceptance.so"]
        },
        "instrumentation": "private bot_tick.cpp execution-wall scope and tickBrain call scope; product source unchanged",
    }
    world = Path("/tmp/canary-lifecycle-qa-world.otbm")
    environment["world_fixture"] = {
        "file": world.name,
        "bytes": world.stat().st_size,
        "sha256": hashlib.sha256(world.read_bytes()).hexdigest(),
        "read_only_mount": True,
    }
    for name in [q.GAME, q.DB]:
        detail = json.loads(q.docker("inspect", name))[0]
        environment[name] = {
            "image_id": detail["Image"],
            "labels": detail["Config"]["Labels"],
            "networks": list(detail["NetworkSettings"]["Networks"]),
            "published_ports": detail["HostConfig"]["PortBindings"],
            "mounts": [
                {"target": m["Destination"], "read_write": m["RW"], "type": m["Type"]}
                for m in detail["Mounts"]
            ],
        }
    q.write_json("party-environment.json", environment)
    inspection = q.docker(
        "exec",
        q.GAME,
        "python3",
        "-c",
        r"""
from pathlib import Path
import hashlib,json,sqlite3
comparison={}
for rel in ['data/scripts','data/bot/authored']:
    root=Path('/qa-repo')/rel; target=Path('/canary')/rel; same=0; different=[]
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix not in {'.lua','.csv'}:continue
        dst=target/p.relative_to(root)
        if dst.exists() and p.read_bytes()==dst.read_bytes():same+=1
        else:different.append(str(p.relative_to('/qa-repo')))
    extra=[str(p.relative_to('/canary')) for p in target.rglob('*.lua') if not (root/p.relative_to(target)).exists()]
    comparison[rel]={'same':same,'different':different,'extra_lua':extra}
paths=['data-otservbr-global/npc/xodet.lua','data/XML/vocations.xml','data/items/items.xml','data-otservbr-global/monster/mammals/wolf.lua']
blobs={}
for rel in paths:
    raw=(Path('/canary')/rel).read_bytes(); data=raw.replace(b'\r\n',b'\n')
    blobs[rel]={'crlf':raw.count(b'\r\n'),'lf_blob':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}
states=[]
for p in Path('/canary').glob('party-*.sqlite3'):
    c=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True)
    count,reserved,spent=c.execute('SELECT COUNT(*),COALESCE(SUM(reserved),0),COALESCE(SUM(spent),0) FROM requests').fetchone()
    pending=c.execute("SELECT COUNT(*) FROM records WHERE kind='pending'").fetchone()[0]
    episodes=[key for key, in c.execute("SELECT key FROM records WHERE kind='episode'")]
    states.append({'file':p.name,'requests':count,'reserved_nanousd':reserved,'spent_nanousd':spent,'durable_pending':pending,'episode_ids':episodes})
    c.close()
print(json.dumps({'source':comparison,'blobs':blobs,'states':states}))
""",
    )
    data = json.loads(inspection)
    assert all(not row["different"] for row in data["source"].values()), data["source"]
    assert data["source"]["data/scripts"]["extra_lua"] == [
        "data/scripts/globalevents/aaa_party_qa.lua"
    ]
    assert all(
        data["blobs"][path]["lf_blob"] == digest for path, digest in DATA_BLOBS.items()
    ), data["blobs"]
    assert all(
        row["requests"] == row["reserved_nanousd"] == row["spent_nanousd"] == 0
        for row in data["states"]
    )
    q.write_json("party-runtime-source-comparison.json", data["source"])
    q.write_json("party-datapack-normalized-blobs.json", data["blobs"])
    functional = None
    scenarios = q.WORK / "party-scenarios-raw.json"
    if scenarios.exists():
        supply = next(
            (
                p
                for p in q.read_json("party-scenarios-raw.json")["phases"]
                if p["name"] == "three_companion_resupply_and_return"
            ),
            None,
        )
        if supply and supply["result"]:
            action = next(iter(supply["result"].values()))["action_id"]
            matched = [r for r in data["states"] if action in r["episode_ids"]]
            assert len(matched) == 1 and matched[0]["durable_pending"] == 0, matched
            functional = matched[0]
    for row in data["states"]:
        row["episodes"] = len(row.pop("episode_ids"))
    financial = {
        "fake_state_files": data["states"],
        "requests_total": 0,
        "reserved_total_nanousd": 0,
        "spent_total_nanousd": 0,
        "functional_state": functional,
    }
    q.write_json("financial-and-pending.json", financial)
    print(
        json.dumps(
            {
                "lua": data["source"]["data/scripts"]["same"],
                "csv": data["source"]["data/bot/authored"]["same"],
                "private_state_files": len(data["states"]),
                "paid_requests": 0,
                "functional_durable_pending": functional["durable_pending"]
                if functional
                else None,
            }
        )
    )


if __name__ == "__main__":
    main()
