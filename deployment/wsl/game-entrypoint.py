"""Render local configuration without logging credentials, then run Canary."""
import json
import os
import shutil
from pathlib import Path


def port(environ, name, default):
    value = environ.get(name, str(default))
    if not value.isdecimal() or not 1 <= int(value) <= 65535:
        raise ValueError(f"{name} must be a TCP port between 1 and 65535")
    return int(value)


def render(environ, config):
    """config.lua.dist plus the deployment overrides; unset QA flags leave the operational output unchanged."""
    login_port = port(environ, "GAME_LOGIN_PORT", 7171)
    game_port = port(environ, "GAME_PROTOCOL_PORT", 7172)
    status_port = port(environ, "GAME_STATUS_PORT", 7173)
    if len({login_port, game_port, status_port}) != 3:
        raise ValueError("game protocol ports must be distinct")

    values = {
        "mysqlHost": "database", "mysqlUser": "canary",
        "mysqlPass": environ["MARIADB_PASSWORD"], "mysqlDatabase": "canary",
        "ip": environ.get("GAME_PUBLIC_IP", "127.0.0.1"),
        "serverName": "Canary bots with cast - WSL",
        "dataPackDirectory": "data-otservbr-global",
    }
    config += "\n-- Local WSL deployment overrides\n"
    config += "\n".join(f"{name} = {json.dumps(value)}" for name, value in values.items())
    config += f"\nmysqlPort = 3306\nloginProtocolPort = {login_port}\ngameProtocolPort = {game_port}\nstatusProtocolPort = {status_port}\n"
    if environ.get("GAME_DISABLE_MAP_DOWNLOAD") == "1":
        config += "toggleDownloadMap = false\n"
    # QA only: the daily global save keeps saving and resetting, but no longer shuts the server down.
    shutdown = environ.get("GAME_DISABLE_GLOBAL_SAVE_SHUTDOWN", "")
    if shutdown not in ("", "1"):
        raise ValueError("GAME_DISABLE_GLOBAL_SAVE_SHUTDOWN must be 1 or unset")
    if shutdown == "1":
        config += "globalServerSaveShutdown = false\n"
    references = environ.get("BOT_POPULATION_REFERENCE_BOTS", "")
    if references:
        if not all(item.isascii() and item.isdecimal() for item in references.split(",")):
            raise ValueError("BOT_POPULATION_REFERENCE_BOTS must be comma-separated GUIDs")
        config += f"botPopulationReferenceBots = {json.dumps(references)}\n"
    config += f"botPlayersOnline = {int(environ.get('BOT_PLAYERS_ONLINE', '997'))}\n"
    config += "enableMetrics = false\n"
    config += 'houseLoseAfterInactivity = 0\nhouseRentPeriod = "never"\n'
    return config


def main():
    Path("config.lua").write_text(render(os.environ, Path("config.lua.dist").read_text()))
    if Path("/etc/canary-brain/server.json").is_file():
        shutil.copyfile("/etc/canary-brain/server.json", "data/bot/brain.json")
    os.execv("/canary/canary", ["/canary/canary"])


if __name__ == "__main__":
    main()
