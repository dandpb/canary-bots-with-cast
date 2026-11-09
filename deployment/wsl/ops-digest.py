#!/usr/bin/env python3
"""Read-only daily ops digest for the canary-bots-wsl Compose deployment.

Collects, without changing anything:

* service health for every container in the ``canary-bots-wsl`` Compose project;
* the native status protocol answer (uptime, protocol version, online players);
* the live Grizzle (bot 65001) state from the brain worker status record;
* the persisted Grizzle row from the game database, to prove XP and level are
  not being lost between saves;
* the last player-save outcome, because a failing save silently drops progress;
* recent error and warning signatures from the game and brain logs;
* reachability of the LiteLLM gateway, the supervision panel and the metrics UI.

Every read is a ``docker inspect`` / ``docker exec`` / HTTP GET / TCP request.
This tool never writes to the database, never inserts a bot command, never
restarts a container and never touches a volume.

Run it from Windows or from WSL; it talks to Docker either way:

    python deployment/wsl/ops-digest.py
    python deployment/wsl/ops-digest.py --json
    python deployment/wsl/ops-digest.py --window 60m --out digest.md
"""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta

PROJECT = "canary-bots-wsl"
GRIZZLE_ID = 65001
STATUS_PORT = 7173
DEFAULT_HISTORY = (
    "/home/daniel/canary-bots-wsl/deployment/wsl/runtime/monitor-grizzle.jsonl"
)
MIN_PLAYERS_ONLINE = 10

# Canary's logger uses year-day-month, not ISO year-month-day. Parse that
# contract before windowing; swapping these fields creates a false clock skew.
APP_TIME_PATTERN = re.compile(r"\[(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})")
DOCKER_TIME_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2}T[0-9:.]+Z)\s")

# Canary logs look like "[2026-06-11 22:34:03.843] [info] ...". Match on the
# level marker, not on words such as "failed" that also appear inside metrics
# of healthy info lines (for example "failed=0").
ERROR_PATTERN = re.compile(r"\[(error|fatal|critical|panic)\]", re.IGNORECASE)
WARNING_PATTERN = re.compile(r"\[(warning|warn)\]", re.IGNORECASE)
TRACEBACK_PATTERN = re.compile(
    r"Traceback \(most recent call last\)|^\s*\w*(Error|Exception):|"
    r"std::terminate|Assertion .*failed|SIGSEGV|SIGABRT",
    re.IGNORECASE,
)
NOISE_PATTERN = re.compile(r"(0x[0-9a-f]+|\b\d{3,}\b|[0-9a-f]{8,})", re.IGNORECASE)
SAVE_PATTERN = re.compile(r"Saving (\d+) players", re.IGNORECASE)
SAVED_PATTERN = re.compile(r"Players saved in ([\d.]+) milliseconds", re.IGNORECASE)
CAPTURE_PATTERN = re.compile(
    r"Captured (\d+) players for server save(?: in [\d.]+ milliseconds)?",
    re.IGNORECASE,
)
COMPLETED_SAVE_PATTERN = re.compile(
    r"Server saved (\d+) players in (\d+(?:\.\d+)?) milliseconds",
    re.IGNORECASE,
)

HIBERNATION_PATTERN = re.compile(
    r"\[BotHibernation\]\s*(\d+) bots:\s*hibernated=(\d+)\s*awake=(\d+)", re.IGNORECASE
)
ACTIVITY_PATTERN = re.compile(r"\[(PTRAIL|MARKET_PASS|BotSupport)\]", re.IGNORECASE)
PAIR_PATTERN = re.compile(r"([A-Za-z][A-Za-z0-9_]*)=('[^']*'|\"[^\"]*\"|\S+)")

WORKER_READ = r"""
import json, sqlite3
db = sqlite3.connect('file:/var/lib/canary-brain/state.sqlite3?mode=ro', uri=True)
row = db.execute("SELECT data FROM records WHERE kind='status' AND key='65001'").fetchone()
item = json.loads(row[0]) if row else {}
keys = ('position', 'objective', 'state', 'health', 'potions', 'xp', 'level',
        'objective_defeats', 'last_observation', 'eligible', 'kills', 'target',
        'waypoint', 'script')
print(json.dumps({k: item.get(k) for k in keys if k in item}))
"""

PLAYER_QUERY = (
    "SELECT id, name, level, experience, health, healthmax, posx, posy, posz, "
    "lastlogin, UNIX_TIMESTAMP() FROM players WHERE id={pid};"
)


def run(args, timeout=25, stdin=None):
    """Run a command and return (stdout, stderr, returncode) without raising."""
    try:
        proc = subprocess.run(
            args,
            check=False,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "", f"timeout after {timeout}s", 124
    except FileNotFoundError as exc:
        return "", str(exc), 127
    return proc.stdout, proc.stderr, proc.returncode


def db_query(sql):
    """Run a read-only SQL statement through the MariaDB container.

    The statement is passed as a positional argument so it is never
    interpolated into the shell command string.
    """
    args = [
        "docker",
        "exec",
        "-i",
        f"{PROJECT}-database-1",
        "sh",
        "-c",
        'MYSQL_PWD="$MARIADB_PASSWORD" mariadb -u canary canary -N -B -e "$1"',
        "sh",
        sql,
    ]
    out, err, code = run(args)
    if code != 0:
        return None, err.strip() or f"exit {code}"
    rows = [line.split("\t") for line in out.strip().splitlines() if line.strip()]
    return rows, None


def compose_containers():
    """Map Compose service name -> container name for the deployment."""
    fmt = '{{.Names}}\t{{.Label "com.docker.compose.service"}}\t{{.State}}\t{{.Status}}'
    out, err, code = run(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            f"label=com.docker.compose.project={PROJECT}",
            "--format",
            fmt,
        ]
    )
    if code != 0:
        return {}, err.strip()
    containers = {}
    for line in out.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        containers[parts[1]] = {
            "container": parts[0],
            "state": parts[2] if len(parts) > 2 else "unknown",
            "status": parts[3] if len(parts) > 3 else "unknown",
        }
    return containers, None


def service_details(containers):
    """Enrich each service with health, uptime and restart count."""
    services = []
    for service, info in sorted(containers.items()):
        out, _, code = run(["docker", "inspect", info["container"]], timeout=20)
        detail = {
            "service": service,
            "container": info["container"],
            "state": info["state"],
            "status": info["status"],
            "health": "none",
            "restarts": None,
            "started_at": None,
            "exit_code": None,
            "uptime_seconds": None,
        }
        if code == 0 and out.strip():
            try:
                meta = json.loads(out)[0]
            except (json.JSONDecodeError, IndexError):
                meta = {}
            state = meta.get("State", {})
            detail["state"] = state.get("Status", detail["state"])
            detail["health"] = (state.get("Health") or {}).get("Status", "none")
            detail["restarts"] = meta.get("RestartCount")
            detail["started_at"] = state.get("StartedAt")
            detail["exit_code"] = state.get("ExitCode")
            detail["uptime_seconds"] = started_ago(state.get("StartedAt"))
        services.append(detail)
    return services


def started_ago(started_at):
    """Seconds since an RFC3339 timestamp, or None when unparsable."""
    if not started_at or started_at.startswith("0001"):
        return None
    try:
        stamp = datetime.fromisoformat(started_at)
    except ValueError:
        return None
    return int((datetime.now(UTC) - stamp).total_seconds())


def native_status(host="127.0.0.1", port=STATUS_PORT, timeout=10):
    """Ask the game server for its status frame (a read-only request)."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as connection:
            connection.settimeout(3)
            connection.sendall(b"\x06\x00\xff\xffinfo")
            chunks = []
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    chunk = connection.recv(65536)
                except TimeoutError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
                if b"</tsqp>" in b"".join(chunks):
                    break
    except OSError as exc:
        return None, f"status port unreachable: {exc}"
    try:
        root = ET.fromstring(b"".join(chunks))
    except ET.ParseError as exc:
        return None, f"unparsable status frame: {exc}"
    server = root.find("serverinfo")
    players = root.find("players")
    monsters = root.find("monsters")
    return {
        "uptime_seconds": int(server.get("uptime", 0)) if server is not None else None,
        "client_protocol": server.get("client") if server is not None else None,
        "server_version": server.get("version") if server is not None else None,
        "server_name": server.get("servername") if server is not None else None,
        "players_online": int(players.get("online", 0))
        if players is not None
        else None,
        "players_max": int(players.get("max", 0)) if players is not None else None,
        "players_peak": int(players.get("peak", 0)) if players is not None else None,
        "monsters": int(monsters.get("total", 0)) if monsters is not None else None,
    }, None


def http_probe(url, timeout=8):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(2048)
            return {
                "url": url,
                "reachable": True,
                "status": response.status,
                "bytes": len(body),
            }
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "reachable": True,
            "status": exc.code,
            "bytes": 0,
            "note": "reachable but not authorized",
        }
    except Exception as exc:  # noqa: BLE001 - the probe reports, never raises
        return {
            "url": url,
            "reachable": False,
            "status": None,
            "note": type(exc).__name__,
        }


def tcp_probe(host, port, timeout=6):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def worker_status(containers):
    """Read the live Grizzle record from the brain worker (read-only SQLite)."""
    brain = containers.get("brain")
    if not brain:
        return None, "brain service is not part of the deployment"
    out, err, code = run(
        ["docker", "exec", brain["container"], "python", "-c", WORKER_READ], timeout=20
    )
    if code != 0:
        return None, err.strip() or f"exit {code}"
    try:
        return json.loads(out.strip() or "{}"), None
    except json.JSONDecodeError as exc:
        return None, f"unreadable worker record: {exc}"


def persisted_player():
    """Read the persisted Grizzle row straight from the game database."""
    rows, error = db_query(PLAYER_QUERY.format(pid=GRIZZLE_ID))
    if error:
        return None, error
    if not rows:
        return None, f"no player row for id {GRIZZLE_ID}"
    row = rows[0]
    names = [
        "id",
        "name",
        "level",
        "experience",
        "health",
        "healthmax",
        "posx",
        "posy",
        "posz",
        "lastlogin",
        "now",
    ]
    values = dict(zip(names, row))
    try:
        return {
            "id": int(values["id"]),
            "name": values["name"],
            "level": int(values["level"]),
            "experience": int(values["experience"]),
            "health": int(values["health"]),
            "healthmax": int(values["healthmax"]),
            "position": [int(values["posx"]), int(values["posy"]), int(values["posz"])],
            "lastlogin": int(values["lastlogin"]),
            "lastlogin_age_seconds": int(values["now"]) - int(values["lastlogin"]),
        }, None
    except (KeyError, ValueError) as exc:
        return None, f"unexpected player row: {exc}"


def parse_duration(text):
    """Turn "30m" / "2h" / "600" / "1d" into a number of seconds."""
    match = re.fullmatch(r"\s*(\d+)\s*([smhd])?\s*", str(text), re.IGNORECASE)
    if not match:
        raise ValueError(f"cannot parse duration: {text!r}")
    amount = int(match.group(1))
    unit = (match.group(2) or "s").lower()
    return amount * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


def app_time(line):
    """Parse the application timestamp a game/brain log line carries."""
    match = APP_TIME_PATTERN.search(line)
    if not match:
        return None
    try:
        return datetime.strptime(
            f"{match.group(1)} {match.group(2)}", "%Y-%d-%m %H:%M:%S"
        )
    except ValueError:
        return None


def log_time(line):
    stamp = app_time(line)
    if stamp is not None:
        return stamp
    match = DOCKER_TIME_PATTERN.match(line)
    if match:
        try:
            return (
                datetime.fromisoformat(match.group(1))
                .astimezone(UTC)
                .replace(tzinfo=None)
            )
        except ValueError:
            pass
    return None


def log_error(line):
    payload = DOCKER_TIME_PATTERN.sub("", line, count=1)
    return bool(
        ERROR_PATTERN.search(payload)
        or TRACEBACK_PATTERN.search(payload)
        or payload.startswith("Companion service stopped:")
    )


def scan_logs(containers, service, window_seconds):
    """Cluster recent error lines into signatures and read save health.

    The window is applied to the application's own timestamps. `docker logs
    --since` is deliberately not used: this collector retains its explicit
    application-log window and understands Canary's year-day-month format.
    """
    info = containers.get(service)
    if not info:
        return None, f"{service} service is not part of the deployment"
    out, err, code = run(
        ["docker", "logs", "--timestamps", "--tail", "5000", info["container"]],
        timeout=45,
    )
    if code != 0:
        return None, err.strip() or f"exit {code}"

    combined = out + "\n" + err
    lines = [line for line in combined.splitlines() if line]
    stamps = [stamp for stamp in (log_time(line) for line in lines) if stamp]
    newest = max(stamps) if stamps else None
    oldest = min(stamps) if stamps else None
    cutoff = (newest - timedelta(seconds=window_seconds)) if newest else None
    if lines and newest is None:
        return (
            None,
            f"{service} log tail has no parseable timestamp; error assessment unavailable",
        )

    selected = []
    unparsed = 0
    for line in lines:
        stamp = log_time(line)
        if stamp is None:
            unparsed += 1
            if log_error(line):
                return (
                    None,
                    f"{service} log contains an error without a timestamp; window unavailable",
                )
            continue
        if cutoff is None or stamp >= cutoff:
            selected.append(line)

    signatures = {}
    errors = 0
    warnings = 0
    for line in selected:
        is_error = log_error(line)
        if is_error:
            errors += 1
        elif WARNING_PATTERN.search(line):
            warnings += 1
        else:
            continue
        signature = NOISE_PATTERN.sub("#", line.strip())[:180]
        signatures[signature] = signatures.get(signature, 0) + 1
    ranked = sorted(signatures.items(), key=lambda kv: kv[1], reverse=True)[:5]
    result = {
        "service": service,
        "window_seconds": window_seconds,
        "lines_in_window": len(selected),
        "lines_without_timestamp": unparsed,
        "error_lines": errors,
        "warning_lines": warnings,
        "top_signatures": [{"count": count, "signature": sig} for sig, count in ranked],
    }
    if newest:
        skew = (datetime.now(UTC).replace(tzinfo=None) - newest).total_seconds()
        result["log_clock"] = {
            "newest_entry": newest.isoformat(),
            "oldest_entry": oldest.isoformat() if oldest else None,
            "skew_seconds": int(skew),
        }
    if service == "game":
        hibernation = HIBERNATION_PATTERN.findall("\n".join(selected))
        result["save_health"] = completed_save_health(selected)
        if hibernation:
            total, hibernated, awake = hibernation[-1]
            result["save_health"]["tracked_bots"] = int(total)
            result["save_health"]["hibernated"] = int(hibernated)
            result["save_health"]["awake"] = int(awake)
        activity = {}
        for tag in ("PTRAIL", "MARKET_PASS", "BotSupport"):
            for line in reversed(selected):
                if f"[{tag}]" not in line:
                    continue
                activity = {
                    key: value.strip("'\"")
                    for key, value in PAIR_PATTERN.findall(line)
                    if key != "source_name"
                }
                activity["_source"] = tag
                break
            if activity:
                break
        if activity:
            result["activity"] = activity
    return result, None


def completed_save_health(lines):
    """Count/duration come from completion; capture alone is not a saved batch."""
    count = duration = pending_count = captured_count = None
    for line in lines:
        capture = CAPTURE_PATTERN.search(line) or SAVE_PATTERN.search(line)
        if capture:
            pending_count = captured_count = int(capture.group(1))
        completed = COMPLETED_SAVE_PATTERN.search(line)
        legacy = SAVED_PATTERN.search(line)
        if completed:
            count = int(completed.group(1))
            duration = float(completed.group(2))
            pending_count = None
        elif legacy:
            # Older completion messages did not include their count. Only pair
            # with a preceding capture in this window, never a later capture.
            count = pending_count
            duration = float(legacy.group(1))
            pending_count = None
    return {
        "last_save_count": count,
        "last_save_milliseconds": duration,
        "last_capture_count": captured_count,
    }


def read_history(path, limit=200):
    """Read the monitor history, from the local path or from WSL."""
    content = None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
    except OSError:
        out, _, code = run(["wsl", "-d", "Ubuntu", "--", "cat", path], timeout=20)
        if code == 0:
            content = out
    if not content:
        return []
    rows = []
    for line in content.splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def latest_history_state(rows):
    """Most recent history row that carries XP/level."""
    for row in reversed(rows):
        if row.get("xp") is not None:
            return row
    return None


def build_digest(args):
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "compose_project": PROJECT,
        "warnings": [],
    }
    containers, error = compose_containers()
    if error:
        report["warnings"].append(f"cannot list Compose services: {error}")
    report["services"] = service_details(containers)

    status, error = native_status(port=args.status_port)
    if error:
        report["warnings"].append(f"native status unavailable: {error}")
    report["status"] = status

    live, error = worker_status(containers)
    if error:
        report["warnings"].append(f"brain worker unreadable: {error}")
    report["grizzle_live"] = live

    persisted, error = persisted_player()
    if error:
        report["warnings"].append(f"persisted player row unreadable: {error}")
    report["grizzle_persisted"] = persisted

    history = read_history(args.history)
    previous = latest_history_state(history)
    report["history"] = {
        "path": args.history,
        "entries": len(history),
        "last_recorded": previous,
    }

    report["logs"] = {}
    for service in ("game", "brain"):
        scan, error = scan_logs(containers, service, args.window_seconds)
        if error:
            report["warnings"].append(f"{service} log scan failed: {error}")
        report["logs"][service] = scan

    report["endpoints"] = {
        "litellm_liveliness": http_probe("http://127.0.0.1:4000/health/liveliness"),
        "supervision_panel": http_probe("http://127.0.0.1:8091/"),
        "metrics_ui": http_probe("http://127.0.0.1:4318/"),
        "web": http_probe("http://127.0.0.1:8080/"),
        "game_status_port": {
            "url": f"tcp://127.0.0.1:{args.status_port}",
            "reachable": tcp_probe("127.0.0.1", args.status_port),
        },
    }
    return report


def evaluate(report):
    """Turn the collected facts into a verdict, findings and next actions."""
    findings = []
    actions = []
    severity = "green"

    def escalate(level):
        order = {"green": 0, "amber": 1, "red": 2}
        nonlocal severity
        if order[level] > order[severity]:
            severity = level

    for warning in report.get("warnings", []):
        escalate("amber")
        findings.append(f"collector evidence incomplete: {warning}")
        actions.append("resolve the collector warning before certifying release health")

    for service in report["services"]:
        if service["state"] != "running":
            escalate("red")
            findings.append(f"service `{service['service']}` is {service['state']}")
            actions.append(f"inspect `{service['service']}` before anything else")
        elif service["health"] == "unhealthy":
            escalate("red")
            findings.append(f"service `{service['service']}` reports unhealthy")
            actions.append(f"review the `{service['service']}` healthcheck output")
        elif service["health"] == "starting":
            escalate("amber")
            findings.append(f"service `{service['service']}` is still starting")
        restarts = service.get("restarts")
        if restarts:
            escalate("amber")
            findings.append(
                f"service `{service['service']}` restarted {restarts} time(s)"
            )
            actions.append(f"check why `{service['service']}` restarted")

    status = report.get("status")
    if not status:
        escalate("red")
        findings.append("the game server did not answer the status request")
        actions.append(
            "confirm the game service is accepting connections on the status port"
        )
    else:
        online = status.get("players_online")
        if online is not None:
            report["population"] = {
                "online": online,
                "peak": status.get("players_peak"),
            }
            if online < 1:
                escalate("red")
                findings.append("no players are online")
                actions.append("check whether the bot population finished loading")
            elif online < MIN_PLAYERS_ONLINE:
                escalate("amber")
                findings.append(f"only {online} players are online")

    live = report.get("grizzle_live")
    if not live:
        escalate(
            "red"
            if any("brain worker unreadable" in w for w in report["warnings"])
            else "amber"
        )
        findings.append("no live Grizzle observation")
        actions.append("check the brain worker container and its SQLite state")
    else:
        observation = live.get("last_observation")
        age = None
        if observation is not None:
            try:
                age = int(datetime.now(UTC).timestamp() - float(observation))
            except (TypeError, ValueError, OverflowError):
                age = None
        if age is None or age < -5:
            escalate("amber")
            findings.append(
                "the live observation timestamp is unavailable or in the future"
            )
        elif age > 60:
            escalate("red")
            findings.append(f"the Grizzle observation is stale ({age}s old)")
            actions.append("confirm the brain worker is still consuming events")
        elif age is not None:
            report["grizzle_age_seconds"] = age

    persisted = report.get("grizzle_persisted")
    if not persisted:
        escalate("amber")
        findings.append(
            "persisted player progress is unavailable; durability is unverified"
        )
    if live and persisted:
        live_xp = live.get("xp")
        live_level = live.get("level")
        numbers = (
            live_xp,
            live_level,
            persisted.get("experience"),
            persisted.get("level"),
        )
        if not all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in numbers
        ):
            escalate("amber")
            findings.append(
                "live or saved progress evidence is incomplete; comparison unavailable"
            )
        elif live_xp > persisted["experience"] or live_level > persisted["level"]:
            escalate("amber")
            findings.append(
                f"live XP {live_xp} is ahead of persisted XP {persisted['experience']} "
                f"(level {live_level} vs {persisted['level']}) - unsaved progress pending"
            )
        elif live_xp < persisted["experience"] or live_level < persisted["level"]:
            escalate("red")
            findings.append(
                f"live XP {live_xp} is behind persisted XP {persisted['experience']} "
                "- the save path may have dropped progress"
            )
            actions.append("compare the player save path before the next restart")
        else:
            findings.append("persisted XP matches the live observation")

    previous = (report.get("history") or {}).get("last_recorded")
    if previous and live:
        report["since_last_record"] = {
            "xp": (live.get("xp") or 0) - (previous.get("xp") or 0),
            "level": (live.get("level") or 0) - (previous.get("level") or 0),
            "floor": ((live.get("position") or [None] * 3)[2] or 0)
            - ((previous.get("position") or [None] * 3)[2] or 0),
        }

    for name, probe in (report.get("endpoints") or {}).items():
        if not probe.get("reachable"):
            escalate("amber")
            findings.append(f"{name} is not reachable")
            actions.append(f"verify {name} before relying on it")

    for service, scan in (report.get("logs") or {}).items():
        if not scan:
            continue
        if scan["error_lines"] > 50:
            escalate("red")
            findings.append(f"{service} logged {scan['error_lines']} error lines")
            actions.append(f"read the top {service} error signatures")
        elif scan["error_lines"]:
            escalate("amber")
            findings.append(f"{service} logged {scan['error_lines']} error lines")
            actions.append(f"read the top {service} error signatures")
        save_health = scan.get("save_health") or {}
        if save_health.get("last_save_count") == 0:
            escalate("red")
            findings.append("the last player save wrote 0 players")
            actions.append("inspect the player save path before the next restart")
        clock = scan.get("log_clock") or {}
        skew = clock.get("skew_seconds")
        if skew is not None and abs(skew) > 300:
            escalate("amber")
            findings.append(
                f"{service} log timestamps are {skew}s away from the host clock "
                f"(newest entry {clock.get('newest_entry')})"
            )
            actions.append(
                f"check the {service} clock source: `docker logs --since` cannot "
                "window this deployment while the skew is present"
            )
        activity = scan.get("activity") or {}
        if activity.get("capRefused") not in (None, "0"):
            escalate("amber")
            findings.append(
                f"the bot engine refused {activity['capRefused']} bot(s) for capacity"
            )
            actions.append("check the bot population cap before the next restart")

    report["verdict"] = severity.upper()
    report["findings"] = findings
    report["next_actions"] = actions
    return report


def render(report):
    """Render the digest as Markdown."""
    lines = []
    lines.append(f"# Canary bots ops digest - {report['generated_at']}")
    lines.append("")
    lines.append(f"**Verdict: {report['verdict']}**")
    lines.append("")

    lines.append("## Services")
    lines.append("")
    lines.append("| Service | State | Health | Restarts | Uptime |")
    lines.append("|---|---|---|---|---|")
    for service in report["services"]:
        uptime = service.get("uptime_seconds")
        uptime_text = (
            "-" if uptime is None else f"{uptime // 3600}h{(uptime % 3600) // 60}m"
        )
        lines.append(
            f"| {service['service']} | {service['state']} | {service['health']} | "
            f"{service.get('restarts', '-')} | {uptime_text} |"
        )
    lines.append("")

    status = report.get("status") or {}
    if status:
        lines.append("## Server")
        lines.append("")
        lines.append(
            f"- Players online: **{status.get('players_online')}** "
            f"(peak {status.get('players_peak')})"
        )
        lines.append(
            f"- Server uptime: {status.get('uptime_seconds')}s, "
            f"protocol {status.get('client_protocol')}, "
            f"version {status.get('server_version')}"
        )
        lines.append(f"- Monsters: {status.get('monsters')}")
        lines.append("")

    lines.append("## Bot activity")
    lines.append("")
    activity = ((report.get("logs") or {}).get("game") or {}).get("activity") or {}
    for key, value in activity.items():
        if key.startswith("_"):
            continue
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("## Grizzle (65001)")
    lines.append("")
    live = report.get("grizzle_live") or {}
    persisted = report.get("grizzle_persisted") or {}
    lines.append("| Field | Live | Persisted |")
    lines.append("|---|---|---|")
    lines.append(f"| XP | {live.get('xp', '-')} | {persisted.get('experience', '-')} |")
    lines.append(
        f"| Level | {live.get('level', '-')} | {persisted.get('level', '-')} |"
    )
    lines.append(
        f"| Position | {live.get('position', '-')} | {persisted.get('position', '-')} |"
    )
    lines.append(
        f"| Health | {live.get('health', '-')} | {persisted.get('health', '-')} |"
    )
    lines.append(f"| Objective | {live.get('objective', '-')} | - |")
    lines.append(f"| Waypoint | {live.get('waypoint', '-')} | - |")
    lines.append("")
    since = report.get("since_last_record")
    if since:
        lines.append(
            f"Since the last monitor record: XP {since['xp']:+d}, "
            f"level {since['level']:+d}, floor {since['floor']:+d}."
        )
        lines.append("")

    lines.append("## Endpoints")
    lines.append("")
    lines.append("| Endpoint | Reachable | Status |")
    lines.append("|---|---|---|")
    for name, probe in (report.get("endpoints") or {}).items():
        status_code = probe.get("status") or ("open" if probe.get("reachable") else "-")
        lines.append(
            f"| {name} | {'yes' if probe.get('reachable') else 'no'} | {status_code} |"
        )
    lines.append("")

    lines.append("## Findings")
    lines.append("")
    if report["findings"]:
        for finding in report["findings"]:
            lines.append(f"- {finding}")
    else:
        lines.append("- nothing to report")
    lines.append("")

    lines.append("## Next actions")
    lines.append("")
    if report["next_actions"]:
        for action in report["next_actions"]:
            lines.append(f"- {action}")
    else:
        lines.append("- none required")
    lines.append("")

    logs = report.get("logs") or {}
    save_health = (logs.get("game") or {}).get("save_health") or {}
    if save_health:
        lines.append("## Save health")
        lines.append("")
        lines.append(
            f"- Last save wrote {save_health.get('last_save_count')} players "
            f"in {save_health.get('last_save_milliseconds')} ms"
        )
        if save_health.get("tracked_bots") is not None:
            lines.append(
                f"- Tracked bots: {save_health.get('tracked_bots')} "
                f"({save_health.get('awake')} awake, "
                f"{save_health.get('hibernated')} hibernated)"
            )
        lines.append("")

    for service, scan in (report.get("logs") or {}).items():
        clock = (scan or {}).get("log_clock") or {}
        if clock.get("skew_seconds") is not None:
            lines.append(
                f"The `{service}` log clock is {clock['skew_seconds']}s away "
                f"from the host clock (newest entry {clock.get('newest_entry')}). "
                "Log windows in this digest are applied on the application's own "
                "timestamps for that reason."
            )
            lines.append("")

    if any(scan and scan.get("error_lines") for scan in logs.values()):
        lines.append("## Error signatures")
        lines.append("")
        for service, scan in logs.items():
            if not scan or not scan.get("error_lines"):
                continue
            lines.append(
                f"**{service}** - {scan['error_lines']} error lines "
                f"in the last {scan['window_seconds']}s "
                f"({scan.get('lines_in_window', 0)} lines)"
            )
            lines.append("")
            for item in scan["top_signatures"]:
                lines.append(f"- ({item['count']}x) `{item['signature']}`")
            lines.append("")

    if report.get("warnings"):
        lines.append("## Collector warnings")
        lines.append("")
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of Markdown"
    )
    parser.add_argument("--out", type=str, help="write the digest to this file")
    parser.add_argument(
        "--window",
        default="30m",
        help="log window for the error scan, e.g. 30m, 2h, 1d",
    )
    parser.add_argument(
        "--history", default=DEFAULT_HISTORY, help="path to monitor-grizzle.jsonl"
    )
    parser.add_argument(
        "--status-port", type=int, default=STATUS_PORT, help="game status port"
    )
    args = parser.parse_args()
    try:
        args.window_seconds = parse_duration(args.window)
    except ValueError as exc:
        parser.error(str(exc))

    report = evaluate(build_digest(args))
    rendered = (
        render(report)
        if not args.json
        else json.dumps(report, ensure_ascii=False, indent=2)
    )
    print(rendered)
    if args.out:
        parent = os.path.dirname(os.path.abspath(args.out))
        os.makedirs(parent, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
