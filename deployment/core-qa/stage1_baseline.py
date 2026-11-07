"""Stage 1 <-> stage 2 of canary-core-qa, measured against the reviewed stage-1 baseline.

The baseline (stage1-baseline.json) was captured read-only on the running stage 1 at
2026-11-06T22:20:30Z and is pinned here by its SHA-256. Its fields fall in two provenance classes,
kept apart in code, receipts and the README:

- historical: containers[].id, containers[].image_id and containers[].created_at. They were
  cross-checked with the historical receipt web-rollout-after.json (its SHA-256 is in the baseline).
- captured_now: network (id, created_at), volumes (name, created_at), Compose labels, container
  state and the DB slice. First read at capture time: compared exactly from then on, never claimed
  as history of the first up.

DB semantics: the upgrade gate needs the DB slice equal to the baseline. After a rollback the slice
may differ (play in stage 1/2 moves characters, XP and items), so the restore check needs the same
volume identity (name and CreatedAt; Docker volumes have no other ID) and current DB integrity
instead. When stage 1 changed before the upgrade, the only path is a new reviewed baseline: `capture`
writes a candidate (captured_now, re-cross-checked with web-rollout-after.json) and a reviewed commit
replaces stage1-baseline.json and BASELINE_SHA256. A mismatch is never accepted silently.

Actions (no action ever runs `down -v` or touches a shared volume):
  check            read-only: the running stage 1 must equal the baseline (the upgrade gate)
  capture          read-only on Docker: write a candidate baseline for review; never pinned by itself
  rollback         stage 2 -> playable stage 1: remove brain and its disposable volumes, re-up stage 1
  verify-restored  read-only: the checks that end `rollback`
  game-rollout-gate  read-only, BEFORE the build: approved clean HEAD, QA Compose contract, stage-1 identities
  game-rollout     read-only: after a game-only rollout, write the game receipt that `capture` accepts

A game-only rollout (e.g. the no-daily-shutdown fix) recreates the game container. Its new ID, image and
CreatedAt are then not history from web-rollout-after.json: `game-rollout` records them in a sealed
game receipt, after checking that database, web, network and the four volumes still equal the pinned
baseline. `capture --game-rollout-receipt` then gives only the game the provenance
game_rollout_<UTC>; database and web stay historical. A DB slice that differs from the pinned baseline
is accepted only with a --db-audit file (who, when, why) that names that exact slice.
"""

import argparse
import hashlib
import json
import os
import re
import socket
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

import preflight as qa
from verify_myaac import verify as verify_myaac

SCHEMA = "stage1-qa-baseline-v1"
BASELINE = qa.HERE / "stage1-baseline.json"  # sanitized and reviewed; captured by Pitagoras on WSL
BASELINE_SHA256 = "272c35fbab6496376a366565ac81368e8885297c1cc9febf7ef73e7cdd554789"
RESTORED = qa.HERE / "runtime/evidence/stage1-restored-receipt.json"
PROVENANCE = {
    "historical": {
        "fields": ["containers[].id", "containers[].image_id", "containers[].created_at"],
        "source": "web-rollout-after.json, cross-checked when the baseline was captured",
    },
    "captured_now": {
        "fields": ["network.id", "network.created_at", "volumes[].name", "volumes[].created_at",
                   "compose_labels", "containers[].status", "containers[].health", "db_logical_snapshot"],
        "source": "first read at baseline capture; compared exactly, not claimed historical",
    },
}
GAME = f"{qa.PROJECT}-game-1"
WEB = f"{qa.PROJECT}-web-1"
DATABASE = f"{qa.PROJECT}-database-1"
BRAIN = f"{qa.PROJECT}-brain-1"
LEDGER = f"{qa.PROJECT}_brain-ledger"
BRAIN_SOCKET = f"{qa.PROJECT}_brain-socket"
REVISION_LABEL = "org.opencontainers.image.revision"
CONTAINER_LABELS = ("config-hash", "project", "service")
GAME_PORTS = {"GAME_LOGIN_PORT": "17171", "GAME_PROTOCOL_PORT": "17172", "GAME_STATUS_PORT": "17173"}
DISABLED_BRAIN = "/etc/canary-core-qa/disabled-brain.json"
LOGIN_URL = "http://127.0.0.1:18080/login.php"
GAME_ROLLOUT_SCHEMA = "qa-game-rollout-v1"
GATE_SCHEMA = "qa-game-rollout-gate-v1"
GATE = qa.HERE / "runtime/evidence/game-rollout-gate.json"
GATE_MAX_AGE = timedelta(hours=12)  # gate -> build -> recreate -> receipt must happen in one sitting
GAME_ROLLOUT_FIELDS = ("id", "image_id", "created_at", "image_source_revision")
GAME_INSPECT = '{"env":{{json .Config.Env}},"ports":{{json .HostConfig.PortBindings}},"mounts":{{json .Mounts}}}'
# Inside the game: only the SHA-256 of config.lua and the effective shutdown value leave it (it holds the
# DB password). Same rule as preflight.lua_setting: the last top-level assignment wins.
GAME_CONFIG_PROBE = (
    "import hashlib, re; b = open('/canary/config.lua', 'rb').read(); "
    f"v = re.findall(r'(?m)^[ \\t]*{qa.SHUTDOWN_KEY}[ \\t]*=[ \\t]*([^\\s-]+)', b.decode()); "
    "print(hashlib.sha256(b).hexdigest(), v[-1] if v else 'missing')"
)
DB_AUDIT_FIELDS = ("auditor", "audited_at_utc", "explanation")
COMPOSE_ENV_DROP = ("MARIADB_PASSWORD", "MARIADB_ROOT_PASSWORD", "BOT_PLAYERS_ONLINE")
STAGE1 = ("docker", "compose", "-p", qa.PROJECT, "-f", "compose.yaml", "--env-file", ".env")
STAGE2 = ("docker", "compose", "-p", qa.PROJECT, "-f", "compose.yaml", "-f", "compose.brain-fake.yaml",
          "--env-file", ".env")

# Docker listing, ID column, Compose key label, expected stage-1 name -> key, allowed stage-2 extras.
LISTINGS = {
    "container": (("docker", "ps", "-a", "--no-trunc"), "{{.ID}}\t{{.Names}}", "service",
                  {f"{qa.PROJECT}-{service}-1": service for service in qa.SERVICES}, {BRAIN: "brain"}),
    "volume": (("docker", "volume", "ls"), "{{.Name}}\t{{.Name}}", "volume",
               {f"{qa.PROJECT}_{volume}": volume for volume in qa.VOLUMES},
               {f"{qa.PROJECT}_{volume}": volume for volume in qa.BRAIN_VOLUMES}),
    "network": (("docker", "network", "ls", "--no-trunc"), "{{.ID}}\t{{.Name}}", "network",
                {f"{qa.PROJECT}_default": "default"}, {}),
}
CONTAINER = ('{"name":{{json .Name}},"id":{{json .Id}},"image_id":{{json .Image}},'
             '"image_ref":{{json .Config.Image}},"created_at":{{json .Created}},'
             '"status":{{json .State.Status}},"health":{{if .State.Health}}{{json .State.Health.Status}}'
             '{{else}}null{{end}},"labels":{{json .Config.Labels}}}')
IMAGE = '{"id":{{json .Id}},"labels":{{json .Config.Labels}}}'
NETWORK = '{"id":{{json .Id}},"name":{{json .Name}},"created_at":{{json .Created}},"labels":{{json .Labels}}}'
VOLUME = '{"name":{{json .Name}},"created_at":{{json .CreatedAt}},"labels":{{json .Labels}}}'

# DB slice, method "qa-character-projection-equivalent-v1". The baseline records the counts, the
# transaction mode and the projection SHA-256 but not its query, so this is a documented equivalent:
# one REPEATABLE READ, READ ONLY transaction WITH CONSISTENT SNAPSHOT; QA characters are the players
# created in QA, i.e. id >= 66100 (prepare.py sets that AUTO_INCREMENT; every seed player is lower).
# The projection SHA-256 is over the exact `mariadb -N -B` bytes of the player and item rows below.
# If it was not Pitagoras's query, the gate refuses (fails closed) until the method is aligned.
QA_PLAYER_FLOOR = 66100
DB_SLICE_METHOD = "qa-character-projection-equivalent-v1"
DB_SLICE_SQL = (
    "SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ; "
    "START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY; "
    "SELECT 'counts', (SELECT COUNT(*) FROM accounts), (SELECT COUNT(*) FROM players), "
    "(SELECT COUNT(*) FROM player_items), "
    f"(SELECT COUNT(*) FROM player_items WHERE player_id >= {QA_PLAYER_FLOOR}); "
    "SELECT 'player', id, account_id, name, level, vocation, experience FROM players "
    f"WHERE id >= {QA_PLAYER_FLOOR} ORDER BY id; "
    "SELECT 'item', player_id, pid, sid, itemtype, count FROM player_items "
    f"WHERE player_id >= {QA_PLAYER_FLOOR} ORDER BY player_id, sid; "
    "COMMIT;"
)
DB_COUNT_KEYS = ("accounts", "players", "player_items", "qa_character_items")
DB_SLICE_SQL_SHA256 = hashlib.sha256(DB_SLICE_SQL.encode()).hexdigest()  # a recaptured baseline pins its exact query
# Restore check: current integrity, not equality with the old slice.
QA_ACCOUNT_FLOOR = 65001  # prepare.py: accounts AUTO_INCREMENT; seeds are 1 (god) and 65000 (bots)
DB_TABLES = ("accounts", "players", "player_items", "player_storage")
DB_INTEGRITY_SQL = (
    "SELECT 'tables', COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name IN ("
    + ", ".join(f"'{table}'" for table in DB_TABLES) + "); "
    f"SELECT 'qa', (SELECT COUNT(*) FROM accounts WHERE id >= {QA_ACCOUNT_FLOOR}), "
    f"(SELECT COUNT(*) FROM players WHERE id >= {QA_PLAYER_FLOOR}); "
    f"CHECK TABLE {', '.join(DB_TABLES)};"
)


def lines(*args):
    return [json.loads(line) for line in qa.command(*args).splitlines() if line.strip()]


def compose_labels(labels, keys=None):
    return {key: value for key, value in sorted((labels or {}).items()) if key.startswith("com.docker.compose.")
            and (keys is None or key.removeprefix("com.docker.compose.") in keys)}


def qa_objects(stage2=False):
    """Every canary-core-qa object by name or label; refuse anything that is not stage 1.

    With stage2=True the brain container and its two disposable volumes are tolerated (rollback).
    Returns the names found per kind.
    """
    found = {}
    for kind, (listing, columns, key, expected, extras) in LISTINGS.items():
        allowed = {**expected, **(extras if stage2 else {})}
        labels = f'\t{{{{.Label "com.docker.compose.project"}}}}\t{{{{.Label "com.docker.compose.{key}"}}}}'
        found[kind] = set()
        for row in qa.command(*listing, "--format", columns + labels).splitlines():
            _ident, name, project, item = (row.split("\t") + ["", "", "", ""])[:4]
            if project == qa.PROJECT or qa.project_name(name):
                if project != qa.PROJECT or allowed.get(name) != item:
                    raise RuntimeError(f"unexpected QA {kind} {name} (project {project or '-'}, {key} "
                                       f"{item or '-'}); refused")
                found[kind].add(name)
        if not set(expected) <= found[kind]:
            missing = ", ".join(sorted(set(expected) - found[kind]))
            raise RuntimeError(f"stage-1 QA {kind}s are incomplete (missing {missing}); refused")
    return found


def assert_images(brain_allowed):
    images = set(qa.command("docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}").splitlines())
    if qa.BRAIN_IMAGE in images and not brain_allowed:
        raise RuntimeError(f"{qa.BRAIN_IMAGE} already exists; stage-1 upgrade refused")
    if not qa.IMAGES <= images:
        raise RuntimeError("stage-1 QA image tags game/web are absent; refused")


def assert_web_image(baseline):
    """The mutable web tag must still resolve to the reviewed stage-1 image."""
    web = next(item for item in baseline["containers"] if item["name"] == WEB)
    try:
        actual = qa.command("docker", "image", "inspect", web["image_ref"], "--format", "{{.Id}}").strip()
    except RuntimeError as error:
        raise RuntimeError("the reviewed stage-1 web image tag is absent; refused") from error
    if actual != web["image_id"]:
        raise RuntimeError(f"stage-1 web image tag {web['image_ref']} resolves to {actual}, "
                           f"expected reviewed {web['image_id']}; refused")


def db_slice():
    """The transactional DB slice: four counts and the QA-character projection SHA-256."""
    rows = mariadb(DB_SLICE_SQL).splitlines()
    counts = [row.split("\t")[1:] for row in rows if row.startswith("counts\t")]
    if len(counts) != 1 or len(counts[0]) != len(DB_COUNT_KEYS):
        raise RuntimeError("DB slice query returned an unexpected shape; refused")
    projection = "".join(row + "\n" for row in rows if row.startswith(("player\t", "item\t")))
    return {"counts": dict(zip(DB_COUNT_KEYS, (int(value) for value in counts[0]), strict=True)),
            "qa_character_projection_sha256": hashlib.sha256(projection.encode()).hexdigest()}


def mariadb(sql):
    return qa.command("docker", "exec", DATABASE, "sh", "-c",
                      'MYSQL_PWD="$MARIADB_PASSWORD" exec mariadb -ucanary -N -B canary -e "$0"', sql)


def db_integrity():
    """Problems with the current DB: reachable, tables present and OK, QA accounts and players exist."""
    try:
        rows = [row.split("\t") for row in mariadb(DB_INTEGRITY_SQL).splitlines()]
    except RuntimeError:
        return ["database: not reachable with the QA user"]
    problems = []
    tables = [row[1:] for row in rows if row[0] == "tables"]
    if tables != [[str(len(DB_TABLES))]]:
        problems.append(f"database: expected tables {', '.join(DB_TABLES)} are not all present")
    qa_rows = [row[1:] for row in rows if row[0] == "qa"]
    if len(qa_rows) != 1 or not all(value.isdigit() and int(value) > 0 for value in qa_rows[0]):
        problems.append("database: no QA account or QA player left")
    checked = {row[0].split(".")[-1]: row[3] for row in rows
               if len(row) == 4 and row[1] == "check" and row[2] == "status"}
    bad = [table for table in DB_TABLES if checked.get(table) != "OK"]
    if bad:
        problems.append(f"database: CHECK TABLE is not OK for {', '.join(bad)}")
    return problems


def observe(db=True):
    """The running stage-1 objects in the baseline schema, with the DB slice unless db=False. Read-only."""
    names = sorted(LISTINGS["container"][3])
    containers = sorted(lines("docker", "inspect", *names, "--format", CONTAINER), key=lambda item: item["name"])
    revisions = {image["id"]: (image["labels"] or {}).get(REVISION_LABEL) or None for image in lines(
        "docker", "image", "inspect", *sorted({item["image_id"] for item in containers}), "--format", IMAGE)}
    network = lines("docker", "network", "inspect", f"{qa.PROJECT}_default", "--format", NETWORK)[0]
    volumes = lines("docker", "volume", "inspect", *sorted(LISTINGS["volume"][3]), "--format", VOLUME)
    return {
        "containers": [{
            "name": item["name"].lstrip("/"), "id": item["id"], "image_id": item["image_id"],
            "image_ref": item["image_ref"], "image_source_revision": revisions.get(item["image_id"]),
            "created_at": item["created_at"], "status": item["status"], "health": item["health"],
            "compose_labels": compose_labels(item["labels"], CONTAINER_LABELS),
        } for item in containers],
        "network": {**{key: network[key] for key in ("id", "name", "created_at")},
                    "compose_labels": compose_labels(network["labels"])},
        "volumes": [{"name": item["name"], "created_at": item["created_at"],
                     "compose_labels": compose_labels(item["labels"])} for item in volumes],
        **({"db_logical_snapshot": db_slice()} if db else {}),
    }


def comparable(snapshot):
    """Exactly what the gate compares, keyed by name; capture metadata is left out."""
    db = snapshot.get("db_logical_snapshot")
    return {
        "containers": {item["name"]: {key: value for key, value in item.items()
                                      if key not in ("historical_comparison", "game_rollout_comparison")}
                       for item in snapshot["containers"]},
        "network": snapshot["network"],
        "volumes": {item["name"]: item for item in snapshot["volumes"]},
        **({"db_slice": {key: db[key] for key in ("counts", "qa_character_projection_sha256")}} if db else {}),
    }


def differences(expected, actual, path=""):
    if isinstance(expected, dict) and isinstance(actual, dict):
        return [change for key in sorted(set(expected) | set(actual))
                for change in differences(expected.get(key), actual.get(key), f"{path}/{key}")]
    return [] if expected == actual else [f"{path}: baseline {expected!r} != now {actual!r}"]


def load_baseline(path=BASELINE, expected_sha256=BASELINE_SHA256):
    content = path.read_bytes() if path.is_file() else b""
    actual = hashlib.sha256(content).hexdigest()
    if not content or actual != expected_sha256:
        raise RuntimeError(f"stage-1 baseline {path.name} is absent or its SHA-256 {actual[:12]}... differs from "
                           f"the pinned {expected_sha256[:12]}...; refused")
    baseline = json.loads(content)
    if baseline.get("schema") != SCHEMA or baseline.get("project") != qa.PROJECT:
        raise RuntimeError("stage-1 baseline schema or project differs; refused")
    rollout = baseline.get("game_rollout_receipt")
    for item in baseline["containers"]:  # only a recaptured baseline with a game receipt may skip history for game
        check = item.get("game_rollout_comparison" if rollout and item["name"] == GAME else "historical_comparison")
        if not check or not all(check.values()):
            raise RuntimeError("stage-1 baseline containers were not cross-checked with the historical receipt")
    return baseline


def provenance(baseline):
    rollout = baseline.get("game_rollout_receipt")
    return {**PROVENANCE, "historical": {**PROVENANCE["historical"], "receipt": baseline["historical_receipt"]},
            "captured_now": {**PROVENANCE["captured_now"], "captured_at_utc": baseline["captured_at_utc"],
                             "db_slice_method": DB_SLICE_METHOD,
                             "db_slice_transaction": baseline["db_logical_snapshot"].get("transaction")},
            **({rollout["provenance"]: {"containers": [GAME], "receipt": rollout}} if rollout else {})}


def assert_stage1_upgrade(path=BASELINE, expected_sha256=BASELINE_SHA256):
    """Stage 1 -> 2 gate: no brain object yet, and the running stage 1 equals the baseline exactly."""
    baseline = load_baseline(path, expected_sha256)
    qa_objects(stage2=False)
    assert_images(brain_allowed=False)
    assert_web_image(baseline)
    pinned_sql = baseline["db_logical_snapshot"].get("sql_sha256")
    if pinned_sql is not None and pinned_sql != DB_SLICE_SQL_SHA256:  # same scope and hash method, or no comparison
        raise RuntimeError("the baseline DB slice was taken with another query; upgrade refused")
    now = comparable(observe())
    changes = differences(comparable(baseline), now)
    if changes:
        raise RuntimeError("stage 1 differs from the reviewed baseline; upgrade refused:\n" + "\n".join(changes))
    return {"baseline_sha256": expected_sha256, "provenance": provenance(baseline), "observed": now}


def game_contract():
    """Restored game runs the stage-1 config: disabled brain, QA ports, no brain socket mount."""
    problems = []
    found = lines("docker", "inspect", GAME, "--format", GAME_INSPECT)
    game = found[0] if found else {"env": [], "ports": {}, "mounts": []}
    env = dict(entry.split("=", 1) for entry in game["env"] or [] if "=" in entry)
    for key, expected in {**GAME_PORTS, "CANARY_BRAIN_CONFIG": DISABLED_BRAIN}.items():
        if env.get(key) != expected:
            problems.append(f"game: {key} is {env.get(key)!r}, expected {expected!r}")
    bindings = {port: [(item.get("HostIp"), item.get("HostPort")) for item in items or []]
                for port, items in (game["ports"] or {}).items()}
    expected_bindings = {f"{port}/tcp": [("127.0.0.1", port)] for port in GAME_PORTS.values()}
    if bindings != expected_bindings:
        problems.append(f"game: published ports {sorted(bindings)} differ from loopback 17171-17173")
    if any(mount.get("Name") == BRAIN_SOCKET for mount in game["mounts"] or []):
        problems.append("game: still mounts the brain socket volume")
    try:  # only the port lines; the rest of config.lua holds the DB password
        ports = qa.command("docker", "exec", WEB, "grep", "-E", "^(login|game|status)ProtocolPort = ",
                           "/canary/config.lua").splitlines()
    except RuntimeError:
        ports = []
    if "gameProtocolPort = 17172" not in ports:
        problems.append(f"web: config.lua advertises {ports or 'no gameProtocolPort'}, expected gameProtocolPort = 17172")
    return problems


def playable():
    problems = []
    for port in GAME_PORTS.values():
        try:
            socket.create_connection(("127.0.0.1", int(port)), 3).close()
        except OSError:
            problems.append(f"game: 127.0.0.1:{port} is not listening")
    request = urllib.request.Request(LOGIN_URL, data=b'{"type":"cacheinfo"}',
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            if b'"playersonline"' not in response.read():
                problems.append("web: login.php answered without playersonline")
    except OSError:
        problems.append(f"web: {LOGIN_URL} is not reachable on loopback")
    return problems


def verify_restored(path=BASELINE, expected_sha256=BASELINE_SHA256, receipt_path=None):
    """After rollback: same stage-1 objects (only game recreated), DB intact, playable. Fails closed.

    The DB slice is not compared: play may change it. Volume identity (name, CreatedAt) is.
    """
    baseline = load_baseline(path, expected_sha256)
    found = qa_objects(stage2=True)
    leftovers = sorted((found["container"] & {BRAIN}) | (found["volume"] & {LEDGER, BRAIN_SOCKET}))
    problems = [f"brain object still present: {name}" for name in leftovers]
    assert_images(brain_allowed=True)  # the brain image may stay; it runs nowhere
    now = comparable(observe(db=False))
    expected = comparable(baseline)
    for field in ("id", "created_at"):  # stage-1 up recreates game without the override; the rest stays
        expected["containers"][GAME][field] = now["containers"].get(GAME, {}).get(field)
    baseline_slice = expected.pop("db_slice")  # not compared after a rollback: play may change it
    integrity = db_integrity()
    problems += differences(expected, now) + integrity + game_contract()
    db_now = None if integrity else db_slice()  # informational only
    try:
        myaac = verify_myaac()
    except Exception as error:  # noqa: BLE001 - any failure of the image-level contract fails the restore closed
        myaac = None
        problems.append(f"verify_myaac: {error}")
    problems += playable()
    if problems:
        raise RuntimeError("stage 1 is not restored:\n" + "\n".join(problems))
    return qa.save_receipt(receipt_path or RESTORED, {
        "schema": SCHEMA + "-restored", "baseline_sha256": expected_sha256, "provenance": provenance(baseline),
        "observed": now, "myaac": myaac, "game_recreated": now["containers"][GAME]["id"],
        "db": {"integrity": "ok", "slice_now_informational": db_now,
               "slice_equals_baseline": db_now == baseline_slice},
        "verified_at_utc": datetime.now(UTC).isoformat(),
    })


def strings(value):
    if isinstance(value, dict):
        return set().union(set(), *(strings(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(set(), *(strings(item) for item in value))
    return {value.removeprefix("sha256:")} if isinstance(value, str) else set()


def dicts(value):
    if isinstance(value, dict):
        yield value
    for item in value.values() if isinstance(value, dict) else value if isinstance(value, list) else ():
        yield from dicts(item)


def matches(known, value):
    """A full ID/time, or a docker short ID (12+ hex) the receipt kept, equals the observed value."""
    value = value.removeprefix("sha256:")
    return any(item == value or (len(item) >= 12 and all(c in "0123456789abcdef" for c in item)
                                 and value.startswith(item)) for item in known)


def historical_comparison(receipt, containers):
    """Per container: one object of the receipt holds its id, image_id and created_at, and no other ID."""
    result = {}
    for item in containers:
        others = [other["id"] for other in containers if other is not item]
        best = {}
        for entry in dicts(receipt):
            known = strings(entry)
            if any(matches(known, other) for other in others):
                continue
            found = {f"{field}_match": matches(known, item[field]) for field in ("id", "image_id", "created_at")}
            if sum(found.values()) > sum(best.values()):
                best = found
        result[item["name"]] = best or {"created_at_match": False, "id_match": False, "image_id_match": False}
    return result


def sealed(receipt):
    """SHA-256 of a receipt's canonical JSON without its own seal."""
    body = {key: value for key, value in receipt.items() if key != "content_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def game_config():
    """The live game config.lua: SHA-256 and effective globalServerSaveShutdown, never its content."""
    found = qa.command("docker", "exec", GAME, "python3", "-c", GAME_CONFIG_PROBE).split()
    if len(found) != 2 or not re.fullmatch(r"[0-9a-f]{64}", found[0]):
        raise RuntimeError("game config.lua probe returned an unexpected shape; refused")
    return {"sha256": found[0], qa.SHUTDOWN_KEY: found[1]}


def assert_preserved(historical_content, historical_name, snapshot, baseline):
    """database and web as in web-rollout-after.json; them, the network and the 4 volumes as in the baseline."""
    comparison = historical_comparison(json.loads(historical_content), snapshot["containers"])
    for name in (DATABASE, WEB):
        if not all(comparison[name].values()):
            raise RuntimeError(f"{name} differs from {historical_name} ({comparison[name]}); refused")
    assert_persistent_stage1(baseline)
    return comparison


def utcnow():
    return datetime.now(UTC)


def docker_time(value):
    """Docker CreatedAt (nanoseconds, Z) as an aware datetime."""
    found = re.fullmatch(r"(.+T\d\d:\d\d:\d\d)(\.\d+)?(Z|[+-]\d\d:\d\d)", value or "")
    if not found:
        raise RuntimeError(f"unexpected Docker time {value!r}; refused")
    return datetime.fromisoformat(found[1] + (found[2] or ".0")[:7] + ("+00:00" if found[3] == "Z" else found[3]))


def game_rollout_gate(approved_revision, historical, output=None, path=BASELINE, expected_sha256=BASELINE_SHA256):
    """BEFORE building the game: approved clean HEAD, the QA Compose contract, and database/web/network/volumes
    and the still-unchanged stage-1 game equal to the pinned baseline. Read-only; the game may be stopped and
    the DB slice is not compared."""
    revision = qa.assert_source(approved_revision)
    qa.assert_compose()
    content = historical.read_bytes() if historical.is_file() else b""
    if not content:
        raise RuntimeError(f"historical receipt {historical} is absent; game rollout gate refused")
    baseline = load_baseline(path, expected_sha256)
    qa_objects(stage2=False)
    assert_images(brain_allowed=False)
    assert_web_image(baseline)
    snapshot = observe(db=False)
    assert_preserved(content, historical.name, snapshot, baseline)
    game = next(item for item in snapshot["containers"] if item["name"] == GAME)
    old = next(item for item in baseline["containers"] if item["name"] == GAME)
    if any(game[key] != old[key] for key in ("id", "image_id", "created_at")):
        raise RuntimeError("game already differs from the pinned baseline; run the gate before the build; refused")
    gate = {"schema": GATE_SCHEMA, "project": qa.PROJECT, "checked_at_utc": utcnow().isoformat(),
            "source_revision": revision, "baseline_sha256": expected_sha256,
            "web_rollout_receipt": {"filename": historical.name, "sha256": hashlib.sha256(content).hexdigest()},
            "stage1_game": {key: game[key] for key in ("id", "image_id", "created_at", "status")}}
    gate["content_sha256"] = sealed(gate)
    output = output or GATE
    return output, qa.save_receipt(output, gate)


def assert_gate(gate_path, revision, content, expected_sha256, game):
    """The pre-build gate exists, is sealed, fresh, for this revision/baseline/web receipt, and predates the game."""
    raw = gate_path.read_bytes() if gate_path.is_file() else b""
    gate = json.loads(raw) if raw else {}
    if gate.get("schema") != GATE_SCHEMA or gate.get("content_sha256") != sealed(gate):
        raise RuntimeError(f"pre-build gate {gate_path.name} is absent or tampered; run game-rollout-gate before "
                           "the build; game receipt refused")
    checked = datetime.fromisoformat(gate["checked_at_utc"])
    if not timedelta(0) <= utcnow() - checked <= GATE_MAX_AGE:
        raise RuntimeError(f"pre-build gate {gate_path.name} is stale; game receipt refused")
    if (gate["source_revision"] != revision or gate["baseline_sha256"] != expected_sha256
            or gate["web_rollout_receipt"]["sha256"] != hashlib.sha256(content).hexdigest()):
        raise RuntimeError(f"pre-build gate {gate_path.name} names another revision, baseline or web receipt; refused")
    if docker_time(game["created_at"]) <= checked or game["id"] == gate["stage1_game"]["id"]:
        raise RuntimeError(f"game was not recreated after the pre-build gate {gate_path.name}; refused")
    return {"filename": gate_path.name, "sha256": hashlib.sha256(raw).hexdigest(), "checked_at_utc": gate["checked_at_utc"]}


def record_game_rollout(historical, output=None, path=BASELINE, expected_sha256=BASELINE_SHA256, gate_path=None):
    """After a game-only rollout: a sealed receipt of the recreated game, written only if the rest is unchanged."""
    revision = os.environ.get("SOURCE_REVISION", "")
    qa.assert_source(revision)
    content = historical.read_bytes() if historical.is_file() else b""
    if not content:
        raise RuntimeError(f"historical receipt {historical} is absent; game receipt refused")
    baseline = load_baseline(path, expected_sha256)
    qa_objects(stage2=False)
    assert_images(brain_allowed=False)
    assert_web_image(baseline)
    snapshot = observe(db=False)
    assert_preserved(content, historical.name, snapshot, baseline)
    game = next(item for item in snapshot["containers"] if item["name"] == GAME)
    old = next(item for item in baseline["containers"] if item["name"] == GAME)
    if game["image_source_revision"] != revision or game["id"] == old["id"]:
        raise RuntimeError("game is not a container recreated from SOURCE_REVISION; game receipt refused")
    gate = assert_gate(gate_path or GATE, revision, content, expected_sha256, game)
    env = dict(entry.split("=", 1) for entry in lines("docker", "inspect", GAME, "--format", GAME_INSPECT)[0]["env"]
               if "=" in entry)
    config = game_config()
    if env.get(qa.SHUTDOWN_FLAG) != "1" or config[qa.SHUTDOWN_KEY] != "false":
        raise RuntimeError(f"live game config.lua does not have {qa.SHUTDOWN_KEY} = false; game receipt refused")
    recorded_at = utcnow()
    receipt = {
        "schema": GAME_ROLLOUT_SCHEMA, "project": qa.PROJECT, "recorded_at_utc": recorded_at.isoformat(),
        "source_revision": revision, "baseline_sha256": expected_sha256,
        "web_rollout_receipt": {"filename": historical.name, "sha256": hashlib.sha256(content).hexdigest()},
        "game": {key: game[key] for key in ("name", "image_ref", *GAME_ROLLOUT_FIELDS)},
        "game_config": config,
        "preserved": [DATABASE, WEB, "network", "volumes"],
        "pre_build_gate": gate,
    }
    receipt["content_sha256"] = sealed(receipt)
    output = output or qa.HERE / f"runtime/evidence/game-rollout-after-{recorded_at:%Y%m%dT%H%M%SZ}.json"
    if output.exists():
        raise RuntimeError(f"{output.name} already exists; game receipt refused")
    return output, qa.save_receipt(output, receipt)


def game_rollout(path, historical_content, snapshot, expected_sha256):
    """The game receipt must be sealed, carry the config check and describe the live game exactly."""
    content = path.read_bytes() if path.is_file() else b""
    receipt = json.loads(content) if content else {}
    if receipt.get("schema") != GAME_ROLLOUT_SCHEMA or receipt.get("content_sha256") != sealed(receipt):
        raise RuntimeError(f"game receipt {path.name} is absent, of another schema or tampered; capture refused")
    config = receipt.get("game_config") or {}
    if config.get(qa.SHUTDOWN_KEY) != "false" or not re.fullmatch(r"[0-9a-f]{64}", str(config.get("sha256"))):
        raise RuntimeError(f"game receipt {path.name} lacks the config check; capture refused")
    if (receipt.get("baseline_sha256") != expected_sha256 or receipt.get("web_rollout_receipt", {}).get("sha256")
            != hashlib.sha256(historical_content).hexdigest()):
        raise RuntimeError(f"game receipt {path.name} names another baseline or web receipt; capture refused")
    game = next(item for item in snapshot["containers"] if item["name"] == GAME)
    comparison = {f"{key}_match": receipt["game"].get(key) == game[key] for key in GAME_ROLLOUT_FIELDS}
    comparison["config_match"] = game_config() == config
    if not all(comparison.values()):
        raise RuntimeError(f"{GAME} differs from {path.name} ({comparison}); capture refused")
    stamp = datetime.fromisoformat(receipt["recorded_at_utc"]).strftime("%Y%m%dT%H%M%SZ")
    return comparison, {"provenance": f"game_rollout_{stamp}", "filename": path.name,
                        "sha256": hashlib.sha256(content).hexdigest(), "recorded_at_utc": receipt["recorded_at_utc"],
                        "source_revision": receipt["source_revision"]}


def db_audit(path, live, expected_sha256):
    """A DB slice that differs from the pinned baseline needs an audit naming that exact slice."""
    content = path.read_bytes() if path and path.is_file() else b""
    audit = json.loads(content) if content else {}
    if (not all(isinstance(audit.get(key), str) and audit[key].strip() for key in DB_AUDIT_FIELDS)
            or audit.get("baseline_sha256") != expected_sha256 or audit.get("db_slice") != live):
        raise RuntimeError("the DB slice differs from the pinned baseline; capture needs --db-audit with "
                           f"{', '.join(DB_AUDIT_FIELDS)}, baseline_sha256 and this db_slice; refused")
    return {**{key: audit[key] for key in DB_AUDIT_FIELDS}, "filename": path.name,
            "sha256": hashlib.sha256(content).hexdigest()}


def capture(historical, output=None, rollout_receipt=None, audit=None, path=BASELINE,
            expected_sha256=BASELINE_SHA256):
    """A candidate baseline of the running stage 1, for review. Read-only on Docker; never pinned here."""
    content = historical.read_bytes() if historical.is_file() else b""
    if not content:
        raise RuntimeError(f"historical receipt {historical} is absent; capture refused")
    baseline = load_baseline(path, expected_sha256)
    qa_objects(stage2=False)
    assert_images(brain_allowed=False)
    captured_at = datetime.now(UTC)
    snapshot = observe()
    comparison = historical_comparison(json.loads(content), snapshot["containers"])
    rollout = None
    if rollout_receipt:
        assert_preserved(content, historical.name, snapshot, baseline)
        rollout_comparison, rollout = game_rollout(rollout_receipt, content, snapshot, expected_sha256)
    for item in snapshot["containers"]:
        if rollout and item["name"] == GAME:  # recreated: provenance game_rollout_<UTC>, never historical
            item["game_rollout_comparison"] = rollout_comparison
            continue
        item["historical_comparison"] = comparison[item["name"]]
        if not all(item["historical_comparison"].values()):
            raise RuntimeError(f"{item['name']} differs from {historical.name} "
                               f"({item['historical_comparison']}); capture refused")
    live = {key: snapshot["db_logical_snapshot"][key] for key in ("counts", "qa_character_projection_sha256")}
    pinned = comparable(baseline)["db_slice"]
    audited = db_audit(audit, live, expected_sha256) if live != pinned or audit else None
    snapshot["db_logical_snapshot"].update(method=DB_SLICE_METHOD, transaction="REPEATABLE READ; READ ONLY; "
                                           "WITH CONSISTENT SNAPSHOT", sql_sha256=DB_SLICE_SQL_SHA256)
    output = output or qa.HERE / f"runtime/evidence/stage1-baseline-candidate-{captured_at:%Y%m%dT%H%M%SZ}.json"
    if output.exists():
        raise RuntimeError(f"{output.name} already exists; capture refused")
    sha = qa.save_receipt(output, {
        "schema": SCHEMA, "project": qa.PROJECT, **snapshot,
        "captured_at_utc": captured_at.isoformat(),
        "provenance": {"historical": PROVENANCE["historical"]["fields"] if not rollout else [
                           f"containers[{name}].{key}" for name in (DATABASE, WEB)
                           for key in ("id", "image_id", "created_at")],
                       "captured_now": PROVENANCE["captured_now"]["fields"],
                       **({rollout["provenance"]: [f"containers[{GAME}].{key}" for key in GAME_ROLLOUT_FIELDS]}
                          if rollout else {})},
        "historical_receipt": {"filename": historical.name, "sha256": hashlib.sha256(content).hexdigest(),
                               "checked_at_utc": captured_at.isoformat()},
        **({"game_rollout_receipt": rollout} if rollout else {}),
        **({"db_audit": audited} if audited else {}),
        "previous_baseline_sha256": expected_sha256,
        "limits": ["Docker inspections and DB slice were sequential, not atomic across systems.",
                   "Network, volumes and the DB slice are captured_now: no historical claim.",
                   "DB data is a point-in-time read-only logical slice, not a full backup."],
    })
    return output, sha


def compose_env():
    env = os.environ.copy()
    if not env.get("SOURCE_REVISION"):
        raise RuntimeError("export SOURCE_REVISION (the stage-2 SHA) so Compose renders; nothing is built")
    for name in COMPOSE_ENV_DROP:
        env.pop(name, None)
    return env


def run(*args, env=None):
    """A mutating step of the rollback: shown, then run; any failure stops the rollback."""
    print("+", " ".join(args), flush=True)
    qa.command(*args, env=env)


def assert_persistent_stage1(baseline):
    """Before rollback mutations, preserve DB/web/network/volume identities and labels.

    The game is intentionally different in stage 2. Status/health are checked after
    restore, not used as resource identities here; DB contents may change through play.
    """
    expected = comparable(baseline)
    expected.pop("db_slice", None)
    now = comparable(observe(db=False))
    for snapshot in (expected, now):
        snapshot["containers"].pop(GAME)
        for item in snapshot["containers"].values():
            item.pop("status")
            item.pop("health")
    changes = differences(expected, now)
    if changes:
        raise RuntimeError("persistent stage-1 resources differ from the reviewed baseline; "
                           "rollback refused:\n" + "\n".join(changes))


def rollback(path=BASELINE, expected_sha256=BASELINE_SHA256, receipt_path=None):
    """Stage 2 -> playable stage 1. Only brain and brain-* go away; database, logs and cache stay."""
    baseline = load_baseline(path, expected_sha256)
    env = compose_env()
    found = qa_objects(stage2=True)
    assert_web_image(baseline)
    assert_persistent_stage1(baseline)
    game_image = next(item["image_id"] for item in baseline["containers"] if item["name"] == GAME)
    try:
        present = qa.command("docker", "image", "inspect", game_image, "--format", "{{.Id}}").strip()
    except RuntimeError:
        present = None
    if present != game_image:
        raise RuntimeError("the stage-1 game image from the baseline is gone; rollback refused")
    if BRAIN in found["container"]:
        run(*STAGE2, "stop", "-t", "180", "brain", "game", env=env)
        evidence = qa.HERE / "runtime/evidence/brain"
        evidence.mkdir(parents=True, exist_ok=True)
        run(*STAGE2, "cp", "brain:/var/lib/canary-human-qa-stage2/.", "runtime/evidence/brain/", env=env)
        run(*STAGE2, "rm", "-f", "brain", env=env)
    else:
        run(*STAGE2, "stop", "-t", "180", "game", env=env)
    if LEDGER in found["volume"]:
        run("docker", "volume", "rm", LEDGER)
    run("docker", "tag", game_image, "canary-core-qa-game:local")
    run(*STAGE1, "up", "-d", "--no-build", "--no-deps", "--wait", "game", env=env)
    if BRAIN_SOCKET in found["volume"]:  # free only now: the stage-2 game mounted it
        run("docker", "volume", "rm", BRAIN_SOCKET)
    return verify_restored(path, expected_sha256, receipt_path)


def print_capture(path, sha):
    print(f"Candidate baseline {path} SHA-256 {sha}. Not pinned: review it, then in one commit copy it to "
          f"{BASELINE.name} and set BASELINE_SHA256 in stage1_baseline.py.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("check", "capture", "rollback", "verify-restored", "game-rollout-gate",
                                           "game-rollout"))
    parser.add_argument("--approved-revision", help="game-rollout-gate: full SHA approved for the rollout")
    parser.add_argument("--historical-receipt", type=Path,
                        help="capture/game-rollout: path to web-rollout-after.json")
    parser.add_argument("--game-rollout-receipt", type=Path, help="capture: the receipt written by game-rollout")
    parser.add_argument("--db-audit", type=Path, help="capture: DB audit JSON when the slice differs from the pin")
    args = parser.parse_args()
    if args.action in ("capture", "game-rollout", "game-rollout-gate") and not args.historical_receipt:
        parser.error(f"{args.action} needs --historical-receipt")
    if args.action == "capture":
        print_capture(*capture(args.historical_receipt, rollout_receipt=args.game_rollout_receipt,
                               audit=args.db_audit))
    elif args.action == "game-rollout-gate":
        path, sha = game_rollout_gate(args.approved_revision, args.historical_receipt)
        print(f"Pre-build gate {path} SHA-256 {sha}. Only now build and recreate the game.")
    elif args.action == "game-rollout":
        path, sha = record_game_rollout(args.historical_receipt)
        print(f"Game rollout receipt {path} SHA-256 {sha}. Pass it to capture with --game-rollout-receipt.")
    elif args.action == "check":
        result = assert_stage1_upgrade()
        print(f"Stage 1 equals the reviewed baseline {result['baseline_sha256']}; nothing was changed.")
    elif args.action == "rollback":
        print("Stage 1 restored and playable; receipt SHA-256:", rollback())
    else:
        print("Stage 1 restored and playable; receipt SHA-256:", verify_restored())


if __name__ == "__main__":
    main()
