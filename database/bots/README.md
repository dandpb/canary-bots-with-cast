# Bot data — `database/bots/`

## Overview
This folder seeds a fresh Canary database with the bot system's runtime data: the
admin account, the bot account and its 997 bot players, the market price
reference, and bot house ownership + furniture.

> **The engine does not read hunt or route data from MySQL.** Since the BOT_CSV
> migration it loads that from `data/bot/authored/*.csv`, which ships in this
> repo — hunt scripts and their waypoints, city routes, POIs, equipment, town
> mapping and travel positions. There is nothing to import for any of it.
> To add or change a hunt script, edit the CSVs — see BOT_SYSTEM_DOCS.md §6c and
> `tools/cfg_importer/`, which imports an OTClient cavebot `.cfg` directly.

## Interface
- `[import.sh:FILES]` — Automated bash importer executing the numbered SQL dumps in foreign-key dependency order (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME`).
- `[00_bot_schema.sql:bot_market_item_prices]`, `[00_bot_schema.sql:bot_hunt_script_stats]` — Bot runtime table DDL (`CREATE TABLE IF NOT EXISTS`).
- `[01_accounts.sql:accounts]` — Seeds the default admin account (`@god` / `god12345`) and the bot account (`id = 65000`).
- `[02_players.sql:players]` — Seeds the `GOD` character and 997 bot player rows.
- `[03_player_storage.sql:player_storage]` — Seeds bot and `GOD` storage grants (mount and outfit unlocks).
- `[11_bot_market_item_prices.sql:bot_market_item_prices]` — Seeds item market/NPC price reference rows.
- `[14_houses.sql:houses]` — Seeds house ownership and metadata (bots own 794 of 993 houses).
- `[15_tile_store.sql:tile_store]` — Seeds serialized house furniture/item tile blobs.
- `[16_runtime_compatibility.sql:bot_state_persistence]`, `[16_runtime_compatibility.sql:bot_startup_config]`, `[16_runtime_compatibility.sql:bot_nav_events]`, `[16_runtime_compatibility.sql:player_charms]`, `[16_runtime_compatibility.sql:players]` — Runtime state/config/navigation table DDL and column width widens (`charm_points`, `max_charm_points`, `onlinetime`).

## Prerequisites

1. A MySQL/MariaDB database created and reachable.
2. The repo-root **`schema.sql`** already imported into it. (This distribution's
   `schema.sql` intentionally does **not** seed the default god account or sample
   characters — those come from the dumps here.)

## Quick import

```bash
DB_HOST=127.0.0.1 DB_USER=root DB_PASS=yourpass DB_NAME=canary ./import.sh
```

Defaults if you omit the variables: host `127.0.0.1`, port `3306`, user `root`,
empty password, database `canary`. Import into a **fresh** database (the data
files use plain `INSERT`s and will conflict on a re-import).

After import, the default admin login is account **`@god`** / password
**`god12345`** — change it after first login.

## Manual import (e.g. MySQL Workbench, no shell)

Run the files in this exact order (foreign-key / dependency order):

| # | File | Contents |
|---|------|----------|
| 00 | `00_bot_schema.sql` | bot table DDL (`CREATE TABLE IF NOT EXISTS`) |
| 01 | `01_accounts.sql` | god account (`@god` / `god12345`) + bot account |
| 02 | `02_players.sql` | the GOD character + 997 bot players |
| 03 | `03_player_storage.sql` | bot/GOD storage (mount & outfit unlocks, etc.) |
| 11 | `11_bot_market_item_prices.sql` | market price reference (see header) |
| 14 | `14_houses.sql` | house ownership + metadata (bots own 794 of 993 houses) |
| 15 | `15_tile_store.sql` | house furniture/items (per-house serialized tile blobs) |
| 16 | `16_runtime_compatibility.sql` | existing runtime state/config/navigation contracts and safe counter widths |

The numbering has gaps because the files that filled them seeded the old
hunt/route/equipment tables. Those are CSV now, and the tables are gone.

The automatic importer includes step 16. Existing installations can apply only
that repeatable repair without importing bot/player rows again; see
[installation compatibility](../../deployment/INSTALLATION_COMPATIBILITY.md).

Then bump the auto-increment so new registrations don't collide with the seeded
bot id range:

```sql
ALTER TABLE `accounts` AUTO_INCREMENT = 65001;
ALTER TABLE `players`  AUTO_INCREMENT = 66100;
```

## Invariants
- `[import.sh:FILES]` requires the repository root `schema.sql` to be imported first and must execute the SQL files in strict foreign-key dependency order (`00` -> `01` -> `02` -> `03` -> `11` -> `14` -> `15` -> `16`) on a fresh database (data dumps use plain `INSERT INTO` statements and fail on duplicate primary keys if re-imported).
- `[import.sh:58]` bumps `accounts` `AUTO_INCREMENT = 65001` and `players` `AUTO_INCREMENT = 66100` so newly registered player accounts and characters never collide with the seeded bot ID space (`account_id = 65000`, player IDs `65001..66004`).
- `[14_houses.sql:houses]` and `[15_tile_store.sql:tile_store]` house IDs are coupled to the bundled `otservbr` map distribution.
- `[16_runtime_compatibility.sql:player_charms]` and `[16_runtime_compatibility.sql:players]` widen `charm_points`/`max_charm_points` to `INT UNSIGNED` and `players.onlinetime` to `BIGINT UNSIGNED` to prevent integer overflow during migrations and saves.

## Side Effects
- `[import.sh:run]` connects to MySQL (`mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "$DB_NAME"`) and creates/populates `bot_market_item_prices`, `bot_hunt_script_stats`, `accounts`, `players`, `player_storage`, `houses`, `tile_store`, `bot_state_persistence`, `bot_startup_config`, and `bot_nav_events`, and alters `player_charms`, `players`, and `accounts` auto-increment counters.

## Notes

- **No personal data.** The god account ships with the documented default
  login (account `@god` / password `god12345`), emails are placeholders, and
  last-login IPs are zeroed. Change the password after first login.
- **Data provenance** (`source` / `source_file`) is generic in the distributed
  authored CSVs; the functional `source_name` routing key on city routes is kept.
  Wiki-derived market prices are attributed under CC BY-SA 3.0 — see the header
  of `11_bot_market_item_prices.sql` and `THIRD_PARTY_NOTICES.md`.
- **House data** (`14_houses.sql` / `15_tile_store.sql`) pre-seeds bot house
  ownership and the furniture in those houses. House ids match the bundled
  `otservbr` map, so import these into the same map distribution. All owned
  houses belong to bots (account `65000`); there is no real-player ownership or
  bid data. Houses left unowned (owner `0`) simply won't render their stored
  items until a bot claims them.
- **Bot count at runtime** is controlled by `botPlayersOnline` in `config.lua`
  (default 500, capped at the 997 seeded). You do not need all of them online.
- To regenerate the bot population at a different size/name-set, see
  `tools/bot_population_generator/`.

## Verification
- Run: `ctest --test-dir build --output-on-failure`

