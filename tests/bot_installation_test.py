"""Opt-in MariaDB regression using an automatically removed test database."""

import argparse
import re
import subprocess
import uuid
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--container", required=True, help="Existing MariaDB test container"
    )
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.container):
        parser.error("invalid container name")
    root = Path(__file__).resolve().parents[1]
    database = "canary_pr_install_" + uuid.uuid4().hex[:12]

    def sql(query, use_database=True, success=True):
        command = [
            "docker",
            "exec",
            "-i",
            args.container,
            "sh",
            "-c",
            'exec mariadb --batch --raw --skip-column-names -uroot -p"$MARIADB_ROOT_PASSWORD" "$@"',
            "mariadb",
        ]
        if use_database:
            command.append(database)
        result = subprocess.run(command, input=query, text=True, capture_output=True, check=False)
        if success and result.returncode:
            raise RuntimeError(result.stderr)
        if not success and result.returncode == 0:
            raise AssertionError(
                "old schema unexpectedly accepted an overflowing value"
            )
        return result.stdout.strip()

    sql(f"CREATE DATABASE `{database}`;", use_database=False)
    try:
        sql("""CREATE TABLE players(id INT PRIMARY KEY, onlinetime INT NOT NULL DEFAULT 0);
            CREATE TABLE player_charms(player_id INT PRIMARY KEY, charm_points SMALLINT NOT NULL,
            max_charm_points SMALLINT NOT NULL);
            INSERT INTO players VALUES(1,2147483647);
            INSERT INTO player_charms VALUES(1,32767,32767);""")
        sql(
            "SET SESSION sql_mode='STRICT_ALL_TABLES'; UPDATE players SET onlinetime=onlinetime+1;",
            success=False,
        )
        sql(
            "SET SESSION sql_mode='STRICT_ALL_TABLES'; UPDATE player_charms SET charm_points=70000;",
            success=False,
        )
        repair = (root / "database/bots/16_runtime_compatibility.sql").read_text()
        sql(repair)
        sql("""UPDATE players SET onlinetime=onlinetime+3600;
            UPDATE player_charms SET charm_points=70000,max_charm_points=90000;
            INSERT INTO bot_state_persistence(guid,name,ai_state) VALUES(1,'Fixture',0);
            INSERT INTO bot_startup_config VALUES('should_restore_states','1');
            INSERT INTO bot_nav_events(event_type,event_count) VALUES('fixture',2);""")
        sql(repair)
        assert sql("SELECT onlinetime FROM players;") == "2147487247"
        assert (
            sql("SELECT charm_points,max_charm_points FROM player_charms;")
            == "70000\t90000"
        )
        assert sql("SELECT name FROM bot_state_persistence;") == "Fixture"
        assert sql("SELECT config_value FROM bot_startup_config;") == "1"
        assert sql("SELECT event_count FROM bot_nav_events;") == "2"
        schema = (root / "schema.sql").read_text()
        migration = (root / "data-otservbr-global/migrations/50.lua").read_text()
        assert "`onlinetime` BIGINT UNSIGNED" in schema
        for column in ("charm_points", "max_charm_points"):
            assert f"`{column}` INT UNSIGNED" in schema
            assert f"`{column}` INT UNSIGNED" in migration
        print(
            "PASS: old overflows reproduced; repair is repeatable and retains runtime state"
        )
    finally:
        sql(f"DROP DATABASE `{database}`;", use_database=False)


if __name__ == "__main__":
    main()
