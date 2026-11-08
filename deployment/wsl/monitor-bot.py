"""Read live Grizzle state without exposing configuration or credentials.

Run with Docker available on Windows or WSL. Native commands only request status.
The worker observation contains live XP; the database player row may be unsaved.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import time


def sql(query):
    return subprocess.run(
        ["docker", "exec", "-i", "canary-bots-wsl-database-1", "sh", "-c",
         'MYSQL_PWD="$MARIADB_PASSWORD" mariadb -u canary canary -N'],
        input=query, text=True, capture_output=True, check=True, timeout=15,
    ).stdout.strip()


def command(name, value):
    row = int(sql(
        f"INSERT INTO bot_commands (bot_name,command) VALUES ('{name}','{value}'); "
        "SELECT LAST_INSERT_ID();"
    ))
    for _ in range(40):
        result = sql(f"SELECT result FROM bot_commands WHERE id={row} AND processed=1;")
        if result and result != "NULL":
            return result
        time.sleep(0.25)
    raise TimeoutError("native status command did not return")


WORKER = r'''
import json, sqlite3
db = sqlite3.connect('file:/var/lib/canary-brain/state.sqlite3?mode=ro', uri=True)
row = db.execute("SELECT data FROM records WHERE kind='status' AND key='65001'").fetchone()
item = json.loads(row[0]) if row else {}
print(json.dumps({k: item.get(k) for k in (
    'position', 'objective', 'state', 'health', 'potions', 'xp', 'level',
    'objective_defeats', 'last_observation', 'eligible')}))
'''


def sample():
    native = command("Grizzle Alyronia", "status")
    bridge = json.loads(command("_global", "brain status"))
    worker = json.loads(subprocess.run(
        ["docker", "exec", "canary-bots-wsl-brain-1", "python", "-c", WORKER],
        text=True, capture_output=True, check=True, timeout=15,
    ).stdout)
    session = next((x for x in bridge.get("sessions", []) if x["bot"] == 65001), {})
    kills = re.search(r"kills=(\d+)", native)
    now = time.time()
    observed = worker.pop("last_observation", None)
    return {
        "at": datetime.now(timezone.utc).isoformat(), "timestamp": now,
        "world": bridge.get("world"), "worker_alive": bridge.get("worker_alive"),
        "observation_age_seconds": round(now - observed, 2) if observed else None,
        **worker, "script": session.get("script"), "waypoint": session.get("waypoint"),
        "running": session.get("running"),
        "native_kills": int(kills[1]) if kills else None,
    }


def assess(rows):
    current = rows[-1]
    if not current.get("worker_alive") or current.get("observation_age_seconds") is None or current["observation_age_seconds"] > 10:
        return "worker_unavailable_or_stale"
    window = [r for r in rows if r.get("world") == current.get("world")
              and r["timestamp"] >= current["timestamp"] - 360]
    if len(window) < 2 or current["timestamp"] - window[0]["timestamp"] < 300:
        return "observing"
    retreat_rows = [row for row in window if row.get("running") and row.get("objective") == "retreat"]
    if (current.get("running") and current.get("objective") == "retreat"
            and len(retreat_rows) >= len(window) * 0.75
            and all(row.get("worker_alive") and row.get("observation_age_seconds") is not None
                    and row["observation_age_seconds"] <= 10 for row in window)
            and all(b["timestamp"] - a["timestamp"] <= 90 for a, b in zip(window, window[1:]))
            and all(b["timestamp"] - a["timestamp"] <= 90 for a, b in zip(retreat_rows, retreat_rows[1:]))):
        positions = [row.get("position") for row in window]
        if all(isinstance(pos, (list, tuple)) and len(pos) == 3 for pos in positions):
            origin = positions[0]
            if all(pos[2] == origin[2] and max(abs(pos[0] - origin[0]), abs(pos[1] - origin[1])) <= 3 for pos in positions):
                return "suspected_retreat_navigation_stall_5_minutes"
    progress = ("position", "objective", "script", "waypoint", "objective_defeats", "native_kills", "xp", "level")
    if any(any(row.get(k) != current.get(k) for k in progress) for row in window):
        return "progress_observed"
    if current.get("running") and current.get("objective") in ("hunt", "retreat", "resupply", "follow"):
        return "suspected_stall_5_minutes"
    return "idle_or_hold"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=0)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--history", type=Path, default=Path(__file__).parent / "runtime" / "monitor-grizzle.jsonl")
    parser.add_argument("--require-floor", type=int)
    parser.add_argument("--require-xp-increase", action="store_true")
    parser.add_argument("--require-level-increase", action="store_true")
    args = parser.parse_args()
    if args.seconds < 0 or args.interval < 1:
        parser.error("seconds must be nonnegative and interval positive")
    rows = []
    if args.history.exists():
        for line in args.history.read_text(encoding="utf-8").splitlines()[-1000:]:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    args.history.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + args.seconds
    reached_floor = False
    initial = None
    gained_xp = False
    gained_level = False
    while True:
        row = sample()
        if initial is None:
            initial = row
        gained_xp |= row.get("xp") is not None and initial.get("xp") is not None and row["xp"] > initial["xp"]
        gained_level |= row.get("level") is not None and initial.get("level") is not None and row["level"] > initial["level"]
        rows.append(row)
        row["assessment"] = assess(rows)
        encoded = json.dumps(row, ensure_ascii=False)
        with args.history.open("a", encoding="utf-8") as output:
            output.write(encoded + "\n")
        print(encoded, flush=True)
        reached_floor |= bool(row.get("position") and row["position"][2] == args.require_floor)
        if time.monotonic() >= deadline:
            break
        time.sleep(min(args.interval, max(0, deadline - time.monotonic())))
    if args.require_floor is not None and not reached_floor:
        raise SystemExit(f"FAIL: never reached floor {args.require_floor}")
    if args.require_xp_increase and not gained_xp:
        raise SystemExit("FAIL: no real XP gain observed")
    if args.require_level_increase and not gained_level:
        raise SystemExit("FAIL: no level increase observed")


if __name__ == "__main__":
    main()
