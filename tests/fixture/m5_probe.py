"""Observe native phase through the read-only status command, never movement orders."""

import json
import subprocess
import sys
import time
from pathlib import Path

from m5_read_state import query

work = Path(sys.argv[1])
last = -100
while not (work / "stop.json").exists():
    lines = (work / "supervisor.jsonl").read_text().splitlines()
    state = json.loads(lines[-1])
    elapsed = state.get("elapsed")
    if elapsed is None or elapsed < 540 or elapsed - last < 10:
        time.sleep(1)
        continue
    last = elapsed
    try:
        identity = int(
            query(
                work,
                "INSERT INTO bot_commands(bot_name,command) VALUES('Grizzle Alyronia','status');SELECT LAST_INSERT_ID();",
            ).strip()
        )
        result = ""
        for _ in range(20):
            result = query(
                work,
                f"SELECT result FROM bot_commands WHERE id={identity} AND processed=1;",
            ).strip()
            if result:
                break
            time.sleep(0.2)
        with (work / "phase-status.jsonl").open("a") as stream:
            stream.write(
                json.dumps(
                    {
                        "elapsed": elapsed,
                        "monotonic": time.monotonic(),
                        "command_id": identity,
                        "status": result,
                    }
                )
                + "\n"
            )
    except (OSError, ValueError, AssertionError, subprocess.SubprocessError) as error:
        with (work / "phase-status.jsonl").open("a") as stream:
            stream.write(
                json.dumps({"elapsed": elapsed, "observer_error": type(error).__name__})
                + "\n"
            )
        break
