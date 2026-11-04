"""Create a fresh, isolated WSL deployment; never overwrite local credentials."""
import json
import os
import secrets
import shutil
from pathlib import Path

here = Path(__file__).resolve().parent
source = here.parent.parent
os.umask(0o077)
for name in ("initdb", "runtime/world", "runtime/config", "runtime/secrets"):
    (here / name).mkdir(parents=True, exist_ok=True)
env = here / ".env"
if not env.exists():
    env.write_text(f"MARIADB_PASSWORD={secrets.token_hex(24)}\nMARIADB_ROOT_PASSWORD={secrets.token_hex(24)}\nGAME_PUBLIC_IP=127.0.0.1\nBOT_PLAYERS_ONLINE=997\n")
shutil.copyfile(source / "schema.sql", here / "initdb/000_schema.sql")
for index, name in enumerate(("00_bot_schema.sql", "01_accounts.sql", "02_players.sql", "03_player_storage.sql", "11_bot_market_item_prices.sql", "14_houses.sql", "15_tile_store.sql"), 10):
    shutil.copyfile(source / "database/bots" / name, here / "initdb" / f"{index:03}_{name}")
(here / "initdb/099_ids.sql").write_text("ALTER TABLE accounts AUTO_INCREMENT = 65001;\nALTER TABLE players AUTO_INCREMENT = 66100;\n")
shutil.copyfile(here / "runtime-schema.sql", here / "initdb/098_runtime.sql")
(here / "initdb").chmod(0o755)
for path in (here / "initdb").glob("*.sql"):
    path.chmod(0o644)
server = {"mode": "active", "bots": [65001, 65004, 65003], "socket_directory": "/run/canary-brain-wsl", "autonomous_bot": 65001}
worker = {"mode": "active", "bots": server["bots"], "socket_directory": server["socket_directory"], "state_file": "/var/lib/canary-brain/state.sqlite3", "credential_file": "/etc/canary-brain/openai.env", "monthly_usd": 50, "decision_timeout": 1.2, "learning": False, "exploration": 0.15, "operator_port": 8091, "operator_host": "0.0.0.0"}
for name, value in (("server.json", server), ("worker.json", worker)):
    path = here / "runtime/config" / name
    if not path.exists():
        path.write_text(json.dumps(value, indent=2) + "\n")
print("Local database configuration and seed files are ready. Existing settings were preserved.")
