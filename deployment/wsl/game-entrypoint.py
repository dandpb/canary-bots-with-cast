"""Render local configuration without logging credentials, then run Canary."""
import json
import os
import shutil
from pathlib import Path

def port(name, default):
    value = os.environ.get(name, str(default))
    if not value.isdecimal() or not 1 <= int(value) <= 65535:
        raise ValueError(f"{name} must be a TCP port between 1 and 65535")
    return int(value)

login_port = port("GAME_LOGIN_PORT", 7171)
game_port = port("GAME_PROTOCOL_PORT", 7172)
status_port = port("GAME_STATUS_PORT", 7173)
if len({login_port, game_port, status_port}) != 3:
    raise ValueError("game protocol ports must be distinct")

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
config += f"\nmysqlPort = 3306\nloginProtocolPort = {login_port}\ngameProtocolPort = {game_port}\nstatusProtocolPort = {status_port}\n"
if os.environ.get("GAME_DISABLE_MAP_DOWNLOAD") == "1":
    config += "toggleDownloadMap = false\n"
references = os.environ.get("BOT_POPULATION_REFERENCE_BOTS", "")
if references:
    if not all(item.isascii() and item.isdecimal() for item in references.split(",")):
        raise ValueError("BOT_POPULATION_REFERENCE_BOTS must be comma-separated GUIDs")
    config += f"botPopulationReferenceBots = {json.dumps(references)}\n"
config += f"botPlayersOnline = {int(os.environ.get('BOT_PLAYERS_ONLINE', '997'))}\n"
config += "enableMetrics = false\n"
config += 'houseLoseAfterInactivity = 0\nhouseRentPeriod = "never"\n'
Path("config.lua").write_text(config)
if Path("/etc/canary-brain/server.json").is_file():
    shutil.copyfile("/etc/canary-brain/server.json", "data/bot/brain.json")
os.execv("/canary/canary", ["/canary/canary"])
