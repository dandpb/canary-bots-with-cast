"""Prepare only the canary-core-qa files; never read the operational WSL runtime."""

import argparse
import hashlib
import os
import secrets
import shutil
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent
MAP_URL = "https://github.com/opentibiabr/canary/releases/download/v3.4.1/otservbr.otbm"
MAP_SHA256 = "a80de1dda6a9aca3956a9d5b7fb2e0caebb451570d26853fc21beb40d5f31da2"
SEEDS = (
    "00_bot_schema.sql", "01_accounts.sql", "02_players.sql",
    "03_player_storage.sql", "11_bot_market_item_prices.sql",
    "14_houses.sql", "15_tile_store.sql",
)


def checked_map(stream, destination):
    temporary = destination.with_suffix(".download")
    digest = hashlib.sha256()
    try:
        with temporary.open("wb") as output:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                output.write(chunk)
                digest.update(chunk)
        if digest.hexdigest() != MAP_SHA256:
            raise ValueError("map SHA-256 does not match the pinned upstream release")
        temporary.chmod(0o644)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    map_source = parser.add_mutually_exclusive_group()
    map_source.add_argument("--map", type=Path, help="copy and verify a downloaded map")
    map_source.add_argument("--download-map", action="store_true", help="download the pinned upstream map")
    map_source.add_argument("--skip-map", action="store_true", help="offline config checks only; do not start services")
    args = parser.parse_args()

    os.umask(0o077)
    initdb = HERE / "runtime/initdb"
    world = HERE / "runtime/world"
    initdb.mkdir(parents=True, exist_ok=True)
    world.mkdir(parents=True, exist_ok=True)
    env = HERE / ".env"
    if not env.exists():
        env.write_text(
            f"MARIADB_PASSWORD={secrets.token_hex(24)}\n"
            f"MARIADB_ROOT_PASSWORD={secrets.token_hex(24)}\n"
            "BOT_PLAYERS_ONLINE=50\n"
        )
    env.chmod(0o600)

    sources = [(SOURCE / "schema.sql", initdb / "000_schema.sql")]
    sources += [(SOURCE / "database/bots" / name, initdb / f"{index:03}_{name}")
                for index, name in enumerate(SEEDS, 10)]
    sources += [(SOURCE / "deployment/wsl/runtime-schema.sql", initdb / "098_runtime.sql")]
    for source, destination in sources:
        shutil.copyfile(source, destination)
        destination.chmod(0o644)
    (initdb / "099_ids.sql").write_text(
        "ALTER TABLE accounts AUTO_INCREMENT = 65001;\n"
        "ALTER TABLE players AUTO_INCREMENT = 66100;\n"
    )
    (initdb / "099_ids.sql").chmod(0o644)
    initdb.chmod(0o755)
    world.chmod(0o755)

    destination = world / "otservbr.otbm"
    if destination.exists():
        with destination.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != MAP_SHA256:
                raise ValueError("existing QA map has the wrong SHA-256")
    elif args.map:
        with args.map.open("rb") as stream:
            checked_map(stream, destination)
    elif args.download_map:
        with urllib.request.urlopen(MAP_URL, timeout=90) as stream:
            checked_map(stream, destination)
    elif not args.skip_map:
        parser.error("provide --map or --download-map before starting QA services")
    print("QA files prepared under deployment/core-qa only; no services were started.")


if __name__ == "__main__":
    main()
