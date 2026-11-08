"""Offline actual Lua producer + Python consumer. No game/server/Docker/DB start."""

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from canary_brain import persistence_witness as w

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import m5_persistence_adapter as adapter
from m5_evidence_manifest import finalize_manifest

BINDING = {
    "run_id": "fresh:native:0",
    "stop_nonce": "a" * 64,
    "bot_id": 65001,
    "native_source": "c" * 40,
    "worker_source": "8" * 40,
    "fixture_sha256": "b" * 64,
    "canary_sha256": "d" * 64,
    "engine_sha256": "e" * 64,
}


def literal(values):
    return (
        "{"
        + ",".join(
            "[" + json.dumps(k) + "]=" + (str(v) if type(v) is int else json.dumps(v))
            for k, v in values.items()
        )
        + "}"
    )


def lua_produce(directory, action="normal"):
    encoder = (HERE.parents[1] / "tests/lua/bot_persistence_no_xp_test.lua").read_text()
    encoder = encoder[
        encoder.index("function qa.encode") : encoder.index("local function snapshot")
    ]
    # Real LuaJIT/OpenSSL hash/syscall writer. Only Game/Player APIs are test doubles.
    code = (
        """local qa={}\n"""
        + encoder
        + """
configManager={getString=function() return "Canary M5 free QA" end};configKeys={SERVER_NAME=1}
GAME_STATE_NORMAL=1;GAME_STATE_SHUTDOWN=2
local epoch=999000; local state=1; local players={}; local logs={};local audit;local swallowed=false
local p={xp=98800,level=20,removed=false}
function p:getGuid() return 65001 end;function p:getId() return 99 end
function p:getExperience() return self.xp end;function p:getLevel() return self.level end
function p:isRemoved() return self.removed end;function p:registerEvent() return true end
players={p}
logger={info=function(line) logs[#logs+1]=line end}
Game={getPlayers=function() return players end,getGameState=function() return state end,
monotonicMs=function() epoch=epoch+1000;return epoch end,
botCommand=function(name,command) assert(name=="_global" and command=="brain status");return '{"world":"world-one","mode":"shadow","roster":[65001]}' end}
"""
        + "local dir="
        + json.dumps(str(directory))
        + "\nlocal action="
        + json.dumps(action)
        + """\n
function Game.setGameState(value)
 local f=assert(io.open(dir.."/audit.jsonl","rb"));local data=f:read("*a");f:close()
 assert(data:find('"kind":"pre_shutdown"',1,true),"snapshot must precede shutdown")
 logs[#logs+1]="Captured 1 players for server save"
 logs[#logs+1]="Server saved 1 players in 1 milliseconds"
 state=value;p.removed=true;players={}
 if action=="mutate" then p.xp=p.xp+1 end
 if action=="shutdown_death" or action=="shutdown_death_error" or action=="shutdown_death_write_error" or action=="shutdown_fault_clear" then
  if action=="shutdown_death_error" then
   local encode=qa.encode
   qa.encode=function(row) if type(row)=="table" and row.kind=="death" then error("injected death serialization failure") end;return encode(row) end
  end
  if action=="shutdown_death_write_error" then
   local ffi=require("ffi");ffi.cdef[[long readlink(const char *, char *, unsigned long);]]
   local encode=qa.encode
   qa.encode=function(row)
    if type(row)=="table" and row.kind=="death" then
     local buf=ffi.new("char[4096]");local found=false
     for fd=3,64 do
      local n=tonumber(ffi.C.readlink("/proc/self/fd/"..fd,buf,4096))
      if n>0 and ffi.string(buf,n)==dir.."/audit.jsonl" then assert(ffi.C.close(fd)==0);found=true;break end
     end
     assert(found,"exact own journal descriptor missing")
    end
    return encode(row)
   end
  end
  -- C8 catches/logs Lua callback errors and ignores its false result. XP is unchanged.
  local ok=pcall(audit.death,p);swallowed=not ok
  if action=="shutdown_fault_clear" then audit.audit_fault=nil;audit.deaths=0 end
 end
 if action=="shutdown_reattach_error" then
  local ok=pcall(audit.attach,p);swallowed=not ok
 end
 return true
end
"""
        + "local module=dofile("
        + json.dumps(str(HERE / "m5_persistence.lua"))
        + ")\naudit=module.new("
        + literal(BINDING)
        + ",dir,function(row) return qa.encode(row) end)\n"
        + """
audit.attach(p);p.xp=100426;audit.think()
if action=="death" then audit.death(p) end
p.xp=100433
local f=assert(io.open(dir.."/stop.request","wb"));f:write("q72-stop-v1\\nfresh:native:0\\n"..string.rep("a",64).."\\n");f:close()
local ok,error=pcall(audit.think)
if action=="late_death" then local lateok=pcall(audit.death,p);swallowed=not lateok end
print(qa.encode({ok=ok,error=tostring(error),logs=logs,swallowed=swallowed,deaths=audit.deaths,audit_fault=audit.audit_fault}))
"""
    )
    script = directory / "driver.lua"
    script.write_text(code)
    process = subprocess.run(
        ["luajit", str(script)], capture_output=True, text=True, check=True, timeout=5
    )
    return json.loads(process.stdout), (directory / "audit.jsonl").read_bytes()


def bundle_fixture(tmp_path):
    output, raw = lua_produce(tmp_path)
    assert output["ok"]
    request = {
        "started": {"wall": 1001.5, "monotonic": 40},
        "published": {"wall": 1001.6, "monotonic": 40.1},
        "request_sha256": w.digest(
            ("q72-stop-v1\nfresh:native:0\n" + "a" * 64 + "\n").encode()
        ),
    }
    with (
        patch.object(w.time, "time", side_effect=[1003.1, 1003.2]),
        patch.object(w.time, "monotonic", side_effect=[41, 41.1]),
    ):
        receipt = w.durable_complete(tmp_path, BINDING, "world-one", request, 0)
    admission = {
        "world": "world-one",
        "bot_id": 65001,
        "captured_ms": 200,
        "deaths": 0,
        "source": "c" * 40,
        "source_dirty": False,
        "nonce": "admit",
    }
    events = [
        {"key": "native-admission", "data": admission},
        {"key": "horizon-final-sample", "data": {"captured_ms": 1800200}},
        {
            "key": "native-terminal-fence",
            "data": {"world": "world-one", "bot_id": 65001, "fence_nonce": "fence"},
        },
        {
            "key": "supervisor-native-qualified",
            "data": {"after_flush": True, "reason": "completed"},
        },
    ]
    for e in events:
        e.update(
            wall=1000 if e["key"] == "native-admission" else 1001,
            kind="lifecycle",
            t_ms=0,
        )
    trial = {
        "persistence_run_id": BINDING["run_id"],
        "persistence_fixture_sha256": "b" * 64,
        "saved_character": {"id": 65001, "level": 20, "experience": 100433},
        "persistence": {
            "contract": w.PROFILE,
            "world": "world-one",
            "bot_id": 65001,
            "game_stop_started_wall": 1001.5,
            "game_stopped_wall": 1003.05,
            "sql_read_started_wall": 1003.3,
            "sql_read_wall": 1003.4,
            "game_stopped_monotonic": 40.9,
            "sql_read_started_monotonic": 41.2,
            "sql_read_monotonic": 41.3,
            "terminal": {
                "binding": BINDING,
                "journal": raw.decode(),
                "durable_complete": receipt,
            },
        },
    }
    return events, trial, output


def test_real_lua_independent_terminal_matches_exact_sql_after_window_gain(tmp_path):
    events, trial, output = bundle_fixture(tmp_path)
    result = w.verify_terminal(events, trial)
    assert result["pre"]["xp"] == result["post"]["xp"] == 100433
    assert result["post"]["removed"] and result["post"]["roster_absent"]
    assert (
        result["post"]["pre_sha256"]
        == hashlib.sha256(
            trial["persistence"]["terminal"]["journal"]
            .encode()
            .splitlines(keepends=True)[-2]
        ).hexdigest()
    )
    adapter.verify_shutdown_logs(
        "\n".join(output["logs"]).encode(), BINDING["stop_nonce"]
    )
    assert (tmp_path / "durable-complete.json").stat().st_mode & 0o777 == 0o600
    assert (tmp_path / "audit.jsonl").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    "case",
    [
        "sql_greater",
        "sql_less",
        "missing_terminal",
        "world",
        "identity",
        "counter_reset",
        "clock_reset",
        "sequence",
        "removed",
        "post_mutation",
        "hash",
        "source",
        "missing_seal",
        "native_short",
        "fixture",
        "run_id",
        "timing",
        "durability",
        "boolean_version",
        "request_hash",
    ],
)
def test_contradictory_or_missing_evidence_fails_closed(tmp_path, case):
    events, trial, _ = bundle_fixture(tmp_path)
    terminal = trial["persistence"]["terminal"]
    receipt = terminal["durable_complete"]
    rows = [json.loads(s) for s in terminal["journal"].splitlines()]
    if case == "sql_greater":
        trial["saved_character"]["experience"] += 1
    elif case == "sql_less":
        trial["saved_character"]["experience"] -= 1
    elif case == "missing_terminal":
        rows.pop()
    elif case == "world":
        rows[-1]["native_status_json"] = (
            '{"world":"replacement","mode":"shadow","roster":[65001]}'
        )
    elif case == "identity":
        rows[-1]["runtime_id"] = 100
    elif case == "counter_reset":
        rows[1]["deaths"] = 1
    elif case == "clock_reset":
        rows[-1]["epoch_ms"] = 0
    elif case == "sequence":
        rows[1]["sequence"] = 9
    elif case == "removed":
        rows[-1]["removed"] = False
    elif case == "post_mutation":
        rows[-1]["xp"] += 1
    elif case == "hash":
        rows[-1]["pre_sha256"] = "0" * 64
    elif case == "source":
        events[0]["data"]["source"] = "0" * 40
    elif case == "missing_seal":
        events.pop()
    elif case == "native_short":
        events[1]["data"]["captured_ms"] -= 1
    elif case == "fixture":
        trial["persistence_fixture_sha256"] = "0" * 64
    elif case == "run_id":
        trial["persistence_run_id"] = "other"
    elif case == "timing":
        trial["persistence"]["sql_read_started_wall"] = 1003
    elif case == "durability":
        receipt["journal_sha256"] = "0" * 64
    elif case == "boolean_version":
        rows[-1]["version"] = True
    elif case == "request_hash":
        receipt["request"]["request_sha256"] = "0" * 64
    if case in {
        "missing_terminal",
        "world",
        "identity",
        "counter_reset",
        "clock_reset",
        "sequence",
        "removed",
        "post_mutation",
        "hash",
        "boolean_version",
    }:
        # Rehash container to ensure semantic rejection, not just checksum failure.
        terminal["journal"] = "".join(json.dumps(r) + "\n" for r in rows)
        receipt["journal_sha256"] = w.digest(terminal["journal"].encode())
        receipt["journal_bytes"] = len(terminal["journal"].encode())
    with pytest.raises((ValueError, StopIteration, KeyError)):
        w.verify_terminal(events, trial)


def test_actual_lua_shutdown_mutation_never_emits_post_seal(tmp_path):
    result, raw = lua_produce(tmp_path, "mutate")
    assert not result["ok"] and b'"kind":"post_remove"' not in raw
    with pytest.raises(ValueError):
        w.parse_journal(raw, BINDING, "world-one")


def test_actual_lua_death_is_preserved_and_rejected(tmp_path):
    result, raw = lua_produce(tmp_path, "death")
    assert not result["ok"] and b'"kind":"death"' in raw
    with pytest.raises(ValueError, match="death"):
        w.parse_journal(raw, BINDING, "world-one")


def test_host_fsync_failure_cannot_publish_complete_or_read_sql(tmp_path):
    _events, trial, _ = bundle_fixture(tmp_path)
    (tmp_path / "durable-complete.json").unlink()
    with (
        patch.object(w.os, "fsync", side_effect=OSError("injected fsync failure")),
        pytest.raises(OSError),
    ):
        w.durable_complete(
            tmp_path,
            BINDING,
            "world-one",
            trial["persistence"]["terminal"]["durable_complete"]["request"],
            0,
        )
    assert not (tmp_path / "durable-complete.json").exists()


def test_producer_is_exclusive_and_host_request_never_overwrites(tmp_path):
    output, raw = lua_produce(tmp_path)
    assert output["ok"]
    with pytest.raises(subprocess.CalledProcessError):
        lua_produce(tmp_path)
    assert (tmp_path / "audit.jsonl").read_bytes() == raw
    with pytest.raises(FileExistsError):
        w.publish_request(tmp_path, BINDING)


def test_actual_generated_overlay_attaches_death_before_activation(tmp_path):
    scripts = tmp_path / "scripts"
    (scripts / "globalevents").mkdir(parents=True)
    (scripts / "lib").mkdir()
    import m5_qa

    # Exercise the actual producer, without running prepare() or Docker.
    (scripts / "globalevents/aaa_m5_free_qa.lua").write_text(m5_qa.live_audit_script())
    shutil.copyfile(
        HERE.parents[1] / "data/scripts/globalevents/bot_manager.lua",
        scripts / "globalevents/bot_manager.lua",
    )
    adapter.render_fixture(scripts, BINDING)
    body = (scripts / "globalevents/bot_manager.lua").read_text()
    assert (
        body.index('player:registerEvent("BotDeath")')
        < body.index("M5PersistenceAudit.attach(player)")
        < body.index(
            "initializeBotQuestAccess(player)",
            body.index("M5PersistenceAudit.attach(player)"),
        )
    )
    assert (scripts / "lib/m5_persistence.lua").read_bytes() == (
        HERE / "m5_persistence.lua"
    ).read_bytes()
    assert json.loads((tmp_path / "persistence-binding.json").read_text()) == BINDING
    subprocess.run(
        [
            "luajit",
            "-b",
            str(scripts / "globalevents/aaa_m5_free_qa.lua"),
            str(tmp_path / "audit.bytecode"),
        ],
        check=True,
        timeout=5,
    )


def test_adapter_requires_real_completed_receipt_before_request_or_sql(tmp_path):
    harness = Mock()
    with pytest.raises(ValueError):
        adapter.stop_and_read(
            harness,
            tmp_path,
            BINDING,
            world="world-one",
            require_native_receipt=lambda: False,
        )
    harness.wait_game.assert_not_called()
    harness.character.assert_not_called()
    assert not (tmp_path / "stop.request").exists()


def test_adapter_timeout_preserves_primary_never_reads_sql(tmp_path):
    failure = TimeoutError("injected owned game wait timeout")
    harness = Mock()
    harness.wait_game.side_effect = failure
    with pytest.raises(TimeoutError) as caught:
        adapter.stop_and_read(
            harness,
            tmp_path,
            BINDING,
            world="world-one",
            require_native_receipt=lambda: True,
        )
    assert caught.value is failure and (tmp_path / "stop.request").is_file()
    harness.character.assert_not_called()


def test_save_failure_logs_reject_even_if_sql_would_match():
    raw = (
        "prefix [M5Persistence] pre "
        + BINDING["stop_nonce"]
        + "\nCaptured 1 players for server save\nServer saved 1 players in 1 milliseconds\n[M5Persistence] post "
        + BINDING["stop_nonce"]
    ).encode()
    adapter.verify_shutdown_logs(raw, BINDING["stop_nonce"])
    for message in [
        b"Failed to durably save",
        b"Could not capture bot",
        b"player failures",
    ]:
        with pytest.raises(ValueError):
            adapter.verify_shutdown_logs(raw + b"\n" + message, BINDING["stop_nonce"])


def test_external_manifest_hashes_completed_collector_stdout(tmp_path):
    log = tmp_path / "collector.log"
    with log.open("xb") as output:
        subprocess.run(
            [
                sys.executable,
                "-c",
                'print("all collector output including final summary")',
            ],
            stdout=output,
            check=True,
            timeout=5,
        )
    manifest = tmp_path / "final.json"
    digest = finalize_manifest([log], manifest)
    assert digest == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert (
        json.loads(manifest.read_text())["artifact_sha256"][str(log)]["sha256"]
        == hashlib.sha256(log.read_bytes()).hexdigest()
    )
    with pytest.raises(FileExistsError):
        finalize_manifest([log], manifest)


def test_manifest_rejects_its_open_stdout_and_selfreference(tmp_path):
    code = """import sys;from pathlib import Path;from m5_evidence_manifest import finalize_manifest
try: finalize_manifest([Path(sys.argv[1])],Path(sys.argv[2]))
except ValueError: sys.exit(0)
sys.exit(3)
"""
    log = tmp_path / "open.log"
    with log.open("xb") as output:
        subprocess.run(
            [sys.executable, "-c", code, str(log), str(tmp_path / "bad.json")],
            env=dict(
                os.environ,
                PYTHONPATH=str(HERE)
                + ":"
                + str(HERE.parents[1] / "deployment/brain/src"),
            ),
            stdout=output,
            check=True,
            timeout=5,
        )
    assert not (tmp_path / "bad.json").exists()
    with pytest.raises(ValueError):
        finalize_manifest([log], log)


def sqlite_report_fixture(tmp_path, telemetry=None):
    import sqlite3

    from canary_brain.recording import Manifest, RecordingStore

    events, trial, _ = bundle_fixture(tmp_path)
    recorder = RecordingStore(tmp_path / "recording.sqlite3")
    recorder.begin(
        Manifest(
            run_id=BINDING["run_id"],
            bot_id=65001,
            lineage="qa",
            provider="native",
            initial_sha256="b" * 64,
        )
    )
    bot = {
        "id": 65001,
        "level": 20,
        "xp": 98800,
        "health": 100,
        "mana": 100,
        "potions": 40,
        "position": [1, 2, 7],
        "alive": True,
        "state": "HUNTING",
    }

    def sample(sequence, captured, xp):
        return {
            "world": "world-one",
            "sequence": sequence,
            "captured_ms": captured,
            "bot": dict(bot, xp=xp),
            "actions": [],
        }

    events[0]["data"].update(phase="native_admitted")
    events[1].update(kind="sample", t_ms=1800000, data=sample(2, 1800200, 100426))
    events.insert(
        0,
        {
            "key": "first",
            "kind": "sample",
            "t_ms": 0,
            "wall": 1000,
            "data": sample(1, 200, 98800),
        },
    )
    if telemetry:
        events[3:3] = telemetry
    for event in events:
        recorder.append({"run": BINDING["run_id"], "segment": "one", **event})
    with sqlite3.connect(tmp_path / "worker.sqlite3") as db:
        db.execute("CREATE TABLE requests(spent INTEGER,reserved INTEGER)")
    trial.update(
        phase="finished",
        stop={"reason": "completed"},
        initial_character={"id": 65001, "level": 20, "experience": 98800},
    )
    (tmp_path / "result.json").write_text(json.dumps(trial))
    spec = importlib.util.spec_from_file_location(
        "actual_fixture_report", HERE / "m5_report.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, trial


def test_real_sqlite_report_keeps_frozen_score_and_exact_terminal_sql_separate(
    tmp_path,
):
    module, trial = sqlite_report_fixture(tmp_path)
    result = module.report(tmp_path)
    assert result["progression"]["errors"] == []
    assert result["progression"]["window"]["xp_delta"] == 1626
    assert result["progression"]["window"]["native_seconds"] == 1800
    assert result["progression"]["persistence_witness"]["post"]["xp"] == 100433
    # Legacy/unknown schema cannot adopt a03's unbound live samples as proof.
    legacy = copy.deepcopy(trial)
    legacy["persistence"].pop("contract")
    legacy["persistence"].pop("terminal")
    (tmp_path / "result.json").write_text(json.dumps(legacy))
    assert "saved_progress_mismatch" in module.report(tmp_path)["progression"]["errors"]
    trial["saved_character"]["experience"] = 100434
    (tmp_path / "result.json").write_text(json.dumps(trial))
    assert any(
        "saved_progress_mismatch" in e
        for e in module.report(tmp_path)["progression"]["errors"]
    )


def test_actual_private_store_reader_reuses_existing_seal_audit(tmp_path):
    import sqlite3
    from types import SimpleNamespace

    import m5_worker

    path = tmp_path / "worker.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE records(kind TEXT,key TEXT,data TEXT)")
        db.execute(
            "INSERT INTO records VALUES(?,?,?)",
            ("run_stop", "end", json.dumps({"reason": "completed"})),
        )
        db.execute(
            "INSERT INTO records VALUES(?,?,?)",
            ("native_admission", BINDING["run_id"], "private-native-admission"),
        )
    config = SimpleNamespace(
        provider="native",
        benchmark_supervision=True,
        state_file=path,
        recording=SimpleNamespace(
            manifests=[SimpleNamespace(run_id=BINDING["run_id"])]
        ),
    )
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with patch.object(m5_worker, "require_final_receipt") as existing:
        assert adapter.production_receipt_check(config) is True
        existing.assert_called_once_with(
            config, {"reason": "completed"}, "private-native-admission"
        )
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    config.provider = "scripted"
    with pytest.raises(ValueError):
        adapter.production_receipt_check(config)


def test_epoch_domain_is_explicit_and_native_monotonic_is_not_relabelled(tmp_path):
    events, trial, _ = bundle_fixture(tmp_path)
    assert events[0]["data"]["captured_ms"] == 200
    result = w.verify_terminal(events, trial)
    assert result["pre"]["clock"] == "unix_epoch_ms"
    assert result["pre"]["epoch_ms"] == 1002000
    # A mismatched epoch label cannot silently become native captured_ms.
    trial["persistence"]["terminal"]["journal"] = trial["persistence"]["terminal"][
        "journal"
    ].replace("unix_epoch_ms", "native_monotonic_ms")
    with pytest.raises(ValueError):
        w.verify_terminal(events, trial)


def test_adapter_orders_native_proof_shutdown_durability_before_sql(tmp_path):
    _events, trial, output = bundle_fixture(tmp_path)
    order = []
    receipt = trial["persistence"]["terminal"]["durable_complete"]
    harness = Mock()
    harness.wait_game.side_effect = lambda **kw: order.append(("wait", kw)) or 0
    harness.shutdown_logs.return_value = "\n".join(output["logs"]).encode()

    def read_sql():
        assert order[-1] == "durable"
        order.append("sql")
        return trial["saved_character"]

    harness.character.side_effect = read_sql

    def require():
        order.append("native-proof")
        return True

    def request(*_):
        order.append("request")
        return receipt["request"]

    def durable(*_):
        order.append("durable")
        return receipt

    with (
        patch.object(adapter, "publish_request", side_effect=request),
        patch.object(adapter, "durable_complete", side_effect=durable),
    ):
        saved, timing, bundle = adapter.stop_and_read(
            harness,
            tmp_path,
            BINDING,
            world="world-one",
            require_native_receipt=require,
        )
    assert order == [
        "native-proof",
        "request",
        ("wait", {"timeout": 210}),
        "durable",
        "sql",
    ]
    assert saved["experience"] == 100433 and bundle["journal"]
    assert (
        timing["game_stopped_monotonic"]
        <= timing["sql_read_started_monotonic"]
        <= timing["sql_read_monotonic"]
    )


def test_nonzero_exit_preserves_journal_and_never_reads_sql(tmp_path):
    harness = Mock()
    harness.wait_game.return_value = 9
    raw = b"preserved incomplete producer bytes\n"
    (tmp_path / "audit.jsonl").write_bytes(raw)
    with pytest.raises(ValueError, match="unclean"):
        adapter.stop_and_read(
            harness,
            tmp_path,
            BINDING,
            world="world-one",
            require_native_receipt=lambda: True,
        )
    harness.character.assert_not_called()
    assert (tmp_path / "audit.jsonl").read_bytes() == raw
    assert not (tmp_path / "durable-complete.json").exists()


def test_sidecar_write_fsync_failure_retains_partial_without_complete(tmp_path):
    _events, trial, _output = bundle_fixture(tmp_path)
    (tmp_path / "durable-complete.json").unlink()
    original = w.os.fsync
    calls = []
    failure = OSError("sidecar fsync failed")

    def fsync(fd):
        calls.append(fd)
        if len(calls) == 3:
            raise failure
        return original(fd)

    with (
        patch.object(w.os, "fsync", side_effect=fsync),
        pytest.raises(OSError) as caught,
    ):
        w.durable_complete(
            tmp_path,
            BINDING,
            "world-one",
            trial["persistence"]["terminal"]["durable_complete"]["request"],
            0,
        )
    assert caught.value is failure
    assert (tmp_path / "durable-complete.json.partial").exists()
    assert not (tmp_path / "durable-complete.json").exists()


def test_host_monotonic_sql_reordering_is_rejected(tmp_path):
    events, trial, _ = bundle_fixture(tmp_path)
    trial["persistence"]["sql_read_started_monotonic"] = 39
    with pytest.raises(ValueError, match="monotonic SQL"):
        w.verify_terminal(events, trial)


@pytest.mark.parametrize("case", ["journal_object", "terminal_null", "sql_list"])
def test_malformed_terminal_schema_rejects_without_attribute_crash(tmp_path, case):
    events, trial, _ = bundle_fixture(tmp_path)
    if case == "journal_object":
        trial["persistence"]["terminal"]["journal"] = {}
    elif case == "terminal_null":
        trial["persistence"]["terminal"] = None
    else:
        trial["saved_character"] = []
    with pytest.raises((TypeError, ValueError)):
        w.verify_terminal(events, trial)


@pytest.mark.parametrize(
    "action",
    [
        "shutdown_death",
        "shutdown_death_error",
        "shutdown_death_write_error",
        "shutdown_reattach_error",
    ],
)
def test_swallowed_shutdown_callback_fault_still_blocks_terminal_seal(tmp_path, action):
    output, raw = lua_produce(tmp_path, action)
    assert not output["ok"] and output["audit_fault"]
    assert b'"kind":"post_remove"' not in raw
    if "death" in action:
        assert output["deaths"] == 1
    if action.endswith("error"):
        assert output["swallowed"] is True
    with pytest.raises((ValueError, KeyError)):
        w.parse_journal(raw, BINDING, "world-one")


def test_late_death_poison_is_retained_after_postseal(tmp_path):
    output, raw = lua_produce(tmp_path, "late_death")
    assert output["ok"] and output["deaths"] == 1 and output["audit_fault"]
    assert b'"kind":"post_remove"' in raw and b'"kind":"death"' in raw
    with pytest.raises(ValueError):
        w.parse_journal(raw, BINDING, "world-one")


def test_crypto_uses_runtime_soname_and_actual_sha256(tmp_path):
    text = (HERE / "m5_persistence.lua").read_text()
    assert 'ffi.load("libcrypto.so.3")' in text and 'ffi.load("crypto")' not in text
    output, raw = lua_produce(tmp_path)
    assert output["ok"]
    lines = raw.splitlines(keepends=True)
    assert json.loads(lines[-1])["pre_sha256"] == hashlib.sha256(lines[-2]).hexdigest()


@pytest.mark.parametrize(
    "error",
    [b"Lua Script Error Detected", b"Call stack overflow. Too many lua script calls"],
)
def test_c8_swallowed_lua_errors_anywhere_in_closed_logs_reject(tmp_path, error):
    output, _raw = lua_produce(tmp_path)
    valid = "\n".join(output["logs"]).encode()
    adapter.verify_shutdown_logs(valid, BINDING["stop_nonce"])
    # Reject also after post marker: a later callback can fail after the pair exists.
    with pytest.raises(ValueError, match="failure"):
        adapter.verify_shutdown_logs(valid + b"\n" + error, BINDING["stop_nonce"])


def test_exposed_diagnostics_cannot_clear_private_sticky_fault(tmp_path):
    output, raw = lua_produce(tmp_path, "shutdown_fault_clear")
    assert not output["ok"] and output["audit_fault"]
    assert b'"kind":"post_remove"' not in raw


@pytest.mark.parametrize(
    "case",
    [
        "zero",
        "window_positive",
        "late_positive",
        "late_bool",
        "late_missing",
        "late_wrong_world",
        "capture_reset",
        "sequence_reset",
    ],
)
def test_real_sqlite_report_and_cli_finalizer_reconcile_full_native_death_stream(
    tmp_path, case
):
    def telemetry(sequence, captured, deaths, late=False):
        data = {
            "world": "world-one",
            "captured_ms": captured,
            "deaths": deaths,
            "phase": "alive",
        }
        return {
            "key": f"native:world-one:65001:{sequence}",
            "kind": "lifecycle",
            "t_ms": 1800001 if late else 1,
            "wall": 1001,
            "data": {"phase": "post_horizon_telemetry", "data": data} if late else data,
        }

    first = telemetry(1, 201, 1 if case == "window_positive" else 0)
    last = telemetry(2, 1800201, 1 if case == "late_positive" else 0, True)
    payload = last["data"]["data"]
    if case == "late_bool":
        payload["deaths"] = False
    if case == "late_missing":
        payload.pop("deaths")
    if case == "late_wrong_world":
        payload["world"] = "other-world"
    if case == "capture_reset":
        payload["captured_ms"] = 200
    if case == "sequence_reset":
        last["key"] = "native:world-one:65001:0"
    module, _trial = sqlite_report_fixture(tmp_path, [first, last])
    report = module.report(tmp_path)
    if case == "zero":
        assert report["progression"]["errors"] == []
    else:
        assert report["progression"]["errors"]
        assert any(
            "terminal_persistence_unverified" in error
            for error in report["progression"]["errors"]
        )
    if case == "window_positive":
        assert report["progression"]["window"]["deaths"] == 1
    if case == "late_positive":
        assert report["progression"]["window"]["deaths"] == 0
    result = subprocess.run(
        [sys.executable, str(HERE / "m5_finalize.py"), str(tmp_path)],
        env=dict(os.environ, PYTHONPATH=str(HERE.parents[1] / "deployment/brain/src")),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == (0 if case == "zero" else 1), result.stderr
    analysis = json.loads((tmp_path / "analysis.json").read_text())
    assert analysis["timed_gate_passed"] is (case == "zero")
    assert analysis["checks"]["window_and_persistence_verified"] is (case == "zero")
    assert analysis["recording_status"] == ("completed" if case == "zero" else "failed")


@pytest.mark.parametrize(
    "case", ["duplicate_conflict", "wrong_bot", "capture_bool", "sample_positive"]
)
def test_zero_death_contract_rejects_conflicting_native_schema(tmp_path, case):
    events, trial, _ = bundle_fixture(tmp_path)
    data = {"world": "world-one", "captured_ms": 201, "phase": "alive", "deaths": 0}
    event = {
        "key": "native:world-one:65001:1",
        "kind": "lifecycle",
        "wall": 1001,
        "t_ms": 1,
        "data": data,
    }
    events.append(event)
    if case == "duplicate_conflict":
        events.append({**event, "data": dict(data, model_owned=True)})
    elif case == "wrong_bot":
        data["bot_id"] = 123
    elif case == "capture_bool":
        data["captured_ms"] = True
    else:
        events.append(
            {
                "key": "late-observation",
                "kind": "lifecycle",
                "wall": 1001,
                "data": {
                    "phase": "post_horizon_sample",
                    "data": {"world": "world-one", "bot": {"id": 65001, "deaths": 1}},
                },
            }
        )
    with pytest.raises(ValueError):
        w.verify_terminal(events, trial)
