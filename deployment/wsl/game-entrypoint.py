"""Render local configuration without logging credentials, then run Canary."""
import json
import os
import shutil
from pathlib import Path

values = {
    "mysqlHost": "database", "mysqlUser": "canary",
    "mysqlPass": os.environ["MARIADB_PASSWORD"], "mysqlDatabase": "canary",
    "ip": os.environ.get("GAME_PUBLIC_IP", "127.0.0.1"),
    "serverName": "Canary bots with cast - WSL",
    "dataPackDirectory": "data-otservbr-global",
}
config = Path("config.lua.dist").read_text()
config += "\n-- Local WSL deployment overrides\n"
config += "\n".join(f"{name} = {json.dumps(value)}" for name, value in values.items())
config += "\nmysqlPort = 3306\nloginProtocolPort = 7171\ngameProtocolPort = 7172\nstatusProtocolPort = 7173\n"
config += f"botPlayersOnline = {int(os.environ.get('BOT_PLAYERS_ONLINE', '997'))}\n"
config += "enableMetrics = false\n"
config += 'houseLoseAfterInactivity = 0\nhouseRentPeriod = "never"\n'
Path("config.lua").write_text(config)
if Path("/etc/canary-brain/server.json").is_file():
    shutil.copyfile("/etc/canary-brain/server.json", "data/bot/brain.json")
os.execv("/canary/canary", ["/canary/canary"])
