"""Add the public 997-bot population to the same disposable QA database only."""

import json
import re
import time

import party_qa as q


def main():
    # Run only after the initial functional scenarios have been archived.
    assert (q.WORK / "party-scenarios-raw.json").is_file()
    phases = q.read_json("party-scenarios-raw.json")["phases"]
    assert {p["name"] for p in phases} == {
        "coordinated_native_hunt",
        "three_companion_resupply_and_return",
        "leader_transfer",
        "worker_loss_fallback",
        "worker_restart",
        "leader_disconnect",
    }
    summary = q.report_directory() / "summary.json"
    assert summary.is_file(), "archive and validate the three-bot scenarios first"
    assert json.loads(summary.read_text()).get("run_id") == q.run_id(), (
        "report belongs to another run"
    )
    q.reserve_output("party-population-load.json")
    q.verify()
    print(q.docker("stop", "-t", "30", q.GAME), flush=True)
    source = (q.ROOT / "database/bots/02_players.sql").read_bytes().decode("latin1")
    statement = re.search(
        r"INSERT INTO `players` .*?;(?=\r?\n)", source, re.DOTALL
    ).group()
    assert "VALUES (65001," in statement or re.search(r"VALUES \(\d+,", statement)
    statement = statement.replace("INSERT INTO", "INSERT IGNORE INTO", 1)
    path = q.WORK / "initdb/999_qa_background.sql"
    path.write_bytes(statement.encode("latin1"))
    db = json.loads(q.docker("inspect", q.DB))[0]
    assert db["Config"]["Labels"].get("canary.qa") == "party"
    assert db["Config"]["Labels"].get("canary.qa.run_id") == q.run_id(), (
        "QA database belongs to another run"
    )
    assert set(db["NetworkSettings"]["Networks"]) == {q.PREFIX}
    assert any(
        m.get("Name") == q.PREFIX + "-data" and m["Destination"] == "/var/lib/mysql"
        for m in db["Mounts"]
    )
    q.docker(
        "exec",
        q.DB,
        "sh",
        "-c",
        "exec mariadb -h127.0.0.1 -ucanary -pparty-qa-only --binary-mode canary < /docker-entrypoint-initdb.d/999_qa_background.sql",
    )
    count = int(q.sql("SELECT COUNT(*) FROM players WHERE account_id=65000"))
    assert count == 997, count
    print(q.docker("start", q.GAME), flush=True)
    time.sleep(7)
    print(q.setup(), flush=True)
    for _ in range(20):
        time.sleep(2)
        players = json.loads(q.command('return PartyQA("inspect")'))
        if all(p["members"] == 5 for p in players):
            break
    else:
        raise AssertionError(players)
    q.command("""BackgroundQA={names={},index=1,loaded=0,errors={}}
local resultId=assert(db.storeQuery("SELECT id,name FROM players WHERE account_id=65000 AND id NOT IN (65001,65003,65004) ORDER BY id"))
repeat BackgroundQA.names[#BackgroundQA.names+1]={guid=result.getNumber(resultId,"id"),name=result.getString(resultId,"name")} until not result.next(resultId)
result.free(resultId)
local function batch()
 for n=1,20 do
  local row=BackgroundQA.names[BackgroundQA.index];if not row then return end
  local p=Game.loadBotPlayer(row.name)
  if p and Game.botActivate(row.guid) then
   Game.botHibernate(row.guid);BackgroundQA.loaded=BackgroundQA.loaded+1
  else BackgroundQA.errors[#BackgroundQA.errors+1]=row.name end
  BackgroundQA.index=BackgroundQA.index+1
 end
 addEvent(batch,50)
end
batch();return {requested=#BackgroundQA.names}""")
    for _ in range(180):
        state = q.command(
            "return {loaded=BackgroundQA.loaded,index=BackgroundQA.index,errors=BackgroundQA.errors,requested=#BackgroundQA.names}"
        )
        print(json.dumps(state), flush=True)
        if state["index"] > state["requested"]:
            break
        time.sleep(1)
    assert state["loaded"] == 994 and not state["errors"], state
    q.write_json("party-population-load.json", state)
    q.command(
        'PartyScenario=dofile("/qa-repo/tests/fixture/party_scenarios.lua");return PartyScenario.baseline()'
    )
    time.sleep(15)
    print("POPULATION_READY", flush=True)


if __name__ == "__main__":
    main()
