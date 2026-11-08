# Docker Runtime Bootstrap & Test Data (`docker/data`)

## Overview
Provides the container startup entrypoint script (`start.sh`) and optional test account/character SQL seed files (`01-test_account.sql`, `02-test_account_players.sql`) for Dockerized Canary deployments.

## Interface
- `[start.sh:OT_DB_HOST]`, `[start.sh:OT_DB_PORT]`, `[start.sh:OT_DB_USER]`, `[start.sh:OT_DB_PASSWORD]`, `[start.sh:OT_DB_DATABASE]`, `[start.sh:OT_SERVER_IP]`, `[start.sh:OT_SERVER_LOGIN_PORT]`, `[start.sh:OT_SERVER_GAME_PORT]`, `[start.sh:OT_SERVER_STATUS_PORT]`, `[start.sh:OT_SERVER_TEST_ACCOUNTS]`, `[start.sh:OT_SERVER_DATA]`, `[start.sh:OT_SERVER_MAP]` — Environment variables configuring container database connection, server ports, data pack, and map download URL.
- `[01-test_account.sql:accounts]` — Inserts test accounts `100` (`dawn`) and `101..115` (`test1..test15`) into `accounts`.
- `[02-test_account_players.sql:players]` — Inserts level 1, 8, and 500 test characters (`Rook Noob *`, `Sorcerer *`, `Druid *`, `Paladin *`, `Knight *`) for accounts `101..115` into `players`.

## Invariants
- `[start.sh:61]` blocks container startup in a retry loop (`sleep 5s`) until the target MySQL server responds to `SHOW DATABASES;`.
- `[start.sh:90]` imports `schema.sql` (and optional test account SQL files when `OT_SERVER_TEST_ACCOUNTS="true"`) only when table `server_config` does not yet exist in `$OT_DB_DATABASE`.

## Side Effects
- `[start.sh:45]` downloads `$OT_SERVER_MAP` via `wget` to `data-otservbr-global/world/otservbr.otbm` when `OT_SERVER_DATA="data-otservbr-global"` and the map file is absent.
- `[start.sh:76]` runs `mysqldump --all-databases >/data/all_databases.sql` if `$OT_DB_DATABASE` already exists, or creates `$OT_DB_DATABASE` (`[start.sh:79]`) and imports `schema.sql` (`[start.sh:94]`).
- `[start.sh:123]` queries `curl ifconfig.me/ip` when `OT_SERVER_IP="auto"`.
- `[start.sh:137]` mutates `config.lua` in-place via `sed -i`, copies `config.lua`, `data/`, and `$OT_SERVER_DATA/` to `/data/server/` if present (`[start.sh:159]`), sets `ulimit -c unlimited`, and replaces the shell process with `exec canary` (`[start.sh:173]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
