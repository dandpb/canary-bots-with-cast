"""Read only named QA character fields and hunt statistics; never provider secrets."""

import json
import subprocess
import sys
from pathlib import Path


def query(directory, sql):
    directory = Path(directory)
    project = json.loads((directory / "result.json").read_text())["project"]
    assert project.startswith("canary-bench-")
    container = project + "-database-1"
    detail = json.loads(subprocess.check_output(["docker", "inspect", container]))[0]
    assert detail["Config"]["Labels"]["com.docker.compose.project"] == project
    assert not detail["HostConfig"]["PortBindings"]
    assert all(m["Source"].startswith(str(directory)) for m in detail["Mounts"])
    args = [
        "docker",
        "exec",
        container,
        "sh",
        "-c",
        'MYSQL_PWD="$MARIADB_PASSWORD" exec mariadb -ucanary canary -N -e "$1"',
        "sh",
        sql,
    ]
    return subprocess.check_output(args, text=True, timeout=15)


def read(directory):
    return query(
        directory,
        "SELECT id,level,experience,vocation,health,healthmax,mana,manamax,balance,skill_sword,skill_shielding,posx,posy,posz FROM players WHERE id=65001; SELECT pid,sid,itemtype,count FROM player_items WHERE player_id=65001 ORDER BY pid,sid; SELECT script_id,successful_hunts,total_kills FROM bot_hunt_script_stats ORDER BY script_id;",
    )


if __name__ == "__main__":
    print(read(sys.argv[1]))
