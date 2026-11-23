# Bot data — `database/bots/`

## Overview
This folder seeds a fresh Canary database with the bot system's runtime data: the
bot account and its 997 bot players, the market price
reference, and bot house ownership + furniture.

> **The engine does not read hunt or route data from MySQL.** Since the BOT_CSV
> migration it loads that from `data/bot/authored/*.csv`, which ships in this
> repo — hunt scripts and their waypoints, city routes, POIs, equipment, town
> mapping and travel positions. There is nothing to import for any of it.
> To add or change a hunt script, edit the CSVs — see BOT_SYSTEM_DOCS.md Â§6c and
> `tools/cfg_importer/`, which imports an OTClient cavebot `.cfg` directly.

## Interface
- `[import.sh:FILES]` — Automated bash importer executing the numbered SQL dumps in foreign-key dependency order (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME`).
- `[00_bot_schema.sql:bot_market_item_prices]`, `[00_bot_schema.sql:bot_hunt_script_stats]` — Bot runtime table DDL (`CREATE TABLE IF NOT EXISTS`).
- `[01_accounts.sql:accounts]` — Seeds the bot account (`id = 65000`).
- `[02_players.sql:players]` — Seeds 997 bot player rows.
- `[03_player_storage.sql:player_storage]` — Seeds bot storage grants.
- `[11_bot_market_item_prices.sql:bot_market_item_prices]` — Seeds item market/NPC price reference rows.
- `[14_houses.sql:houses]` — Seeds house ownership and metadata (bots own 794 of 993 houses).
- `[15_tile_store.sql:tile_store]` — Seeds serialized house furniture/item tile blobs.
- `[16_runtime_compatibility.sql:bot_state_persistence]`, `[16_runtime_compatibility.sql:bot_startup_config]`, `[16_runtime_compatibility.sql:bot_nav_events]`, `[16_runtime_compatibility.sql:player_charms]`, `[16_runtime_compatibility.sql:players]` — Runtime state/config/navigation table DDL and column width widens (`charm_points`, `max_charm_points`, `onlinetime`).

## Prerequisites

1. A MySQL/MariaDB database created and reachable.
2. The repo-root **`schema.sql`** already imported into it. The seed files here
   add the bot account and characters. Provision administrator accounts separately.

## Quick import

```bash
DB_HOST=127.0.0.1 DB_USER=root DB_PASS=yourpass DB_NAME=canary bash database/bots/import.sh
```

Defaults if you omit the variables: host `127.0.0.1`, port `3306`, user `root`,
empty password, database `canary`. Import into a **fresh** database (the data
files use plain `INSERT`s and will conflict on a re-import).

The fresh seed creates the bot account and 997 bot characters.

### Administrator provisioning and rotation

Create an account and character through the deployment's normal registration.
Set a unique password in the protected MyAAC account flow. An authorized
database operator can elevate the selected account and character by their
numeric IDs. The shipped data packs use account type 6 and character group 6
for the GOD role.

On upgrade, rotate the legacy administrator's password through the existing
protected MyAAC password reset or local account administration path. Keep the
account ID, character ownership, account type and character group. Revoke old
sessions for that account. Use a trusted local or HTTPS session for rotation
and leave credentials and password hashes out of command arguments, terminal
history, logs and QA records. Verify ordinary and administrator logins
separately and record only their outcomes.

## Manual import (e.g. MySQL Workbench, no shell)

Run the files in this exact order (foreign-key / dependency order):

| # | File | Contents |
|---|------|----------|
| 00 | `00_bot_schema.sql` | all bot table DDL (`CREATE TABLE IF NOT EXISTS`), including the runtime/telemetry tables `bot_active_players`, `bot_commands`, `bot_chat_emissions`, `bot_hub_presence_60s` |
| 01 | `01_accounts.sql` | bot account |
| 02 | `02_players.sql` | 997 bot players |
| 03 | `03_player_storage.sql` | bot storage grants |
| 11 | `11_bot_market_item_prices.sql` | market price reference (see header) |
| 14 | `14_houses.sql` | house ownership + metadata (bots own 794 of 993 houses) |
| 15 | `15_tile_store.sql` | house furniture/items (per-house serialized tile blobs) |
| 16 | `16_runtime_compatibility.sql` | runtime tables the engine/Lua write (`bot_state_persistence`, `bot_startup_config`, `bot_nav_events`, `bot_test_commands`) + widens `players.onlinetime` and the `player_charms` counters on databases created from an older `schema.sql`. Safe to re-run. |
| 23 | `23_bot_onlinetime_reset.sql` | zeroes the bot account's garbage `onlinetime`. Run with canary stopped. |
| 24 | `24_bot_state_persistence_saved_at.sql` | adds `bot_state_persistence.saved_at`; the engine restores only tasks saved within 24 h. Idempotent. **Must run before** an engine built with it starts. |
| 25 | `25_bot_hunt_danger.sql` | creates `bot_hunt_danger` (learned hunt-danger zones; also in `00_bot_schema.sql`). Idempotent; safe with canary up. Without it zones are memory-only. |

The numbering has gaps because the files that filled them seeded the old
hunt/route/equipment tables. Those are CSV now, and the tables are gone.

The automatic importer includes steps 16–25. Existing installations can apply only
those repeatable repairs without importing bot/player rows again; see
[installation compatibility](../../deployment/INSTALLATION_COMPATIBILITY.md).

Then bump the auto-increment so new registrations don't collide with the seeded
bot id range:

```sql
ALTER TABLE `accounts` AUTO_INCREMENT = 65001;
ALTER TABLE `players`  AUTO_INCREMENT = 66100;
```

## Invariants
- `[import.sh:FILES]` requires the repository root `schema.sql` to be imported first and must execute the SQL files in strict foreign-key dependency order (`00` -> `01` -> `02` -> `03` -> `11` -> `14` -> `15` -> `16` -> `23` -> `24` -> `25`) on a fresh database (data dumps use plain `INSERT INTO` statements and fail on duplicate primary keys if re-imported).
- `[import.sh]` bumps `accounts` `AUTO_INCREMENT = 65001` and `players` `AUTO_INCREMENT = 66100` so newly registered player accounts and characters never collide with the seeded bot ID space (`account_id = 65000`, player IDs `65001..66004`).
- `[14_houses.sql:houses]` and `[15_tile_store.sql:tile_store]` house IDs are coupled to the bundled `otservbr` map distribution.
- `[16_runtime_compatibility.sql:player_charms]` and `[16_runtime_compatibility.sql:players]` widen `charm_points`/`max_charm_points` to `INT UNSIGNED` and `players.onlinetime` to `BIGINT UNSIGNED` to prevent integer overflow during migrations and saves.

## Side Effects
- `[import.sh:run]` connects to MySQL (`mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "$DB_NAME"`) and creates/populates `bot_market_item_prices`, `bot_hunt_script_stats`, `accounts`, `players`, `player_storage`, `houses`, `tile_store`, `bot_state_persistence`, `bot_startup_config`, `bot_nav_events`, and `bot_test_commands`, and alters `player_charms`, `players`, and `accounts` auto-increment counters.

## Schema and `db_version`

- The bot schema is **not** a numbered migration. `data-otservbr-global/migrations/` holds
  upstream's files only, so `db_version` tracks upstream and upstream's own migrations always
  apply. `tools/fork_delta_check.sh` fails if a fork-owned file appears there (#150).
- `91_upstream_1525_schema.sql` is a **cutover-only** script, not part of the import above. It
  reconciles a database last used by the 15.00 bot server (which our old `62.lua` left at
  `db_version=62`) with upstream's migrations 56-59 and sets `db_version=59`. Run it once, with
  canary stopped and after a mysqldump, before the 15.25 port binary first starts. It is
  idempotent.

## Notes

- **No personal data.** No administrator or real-player account is pre-seeded in `01_accounts.sql`; last-login IPs are zeroed. Provision administrators separately following *Administrator provisioning and rotation* above.
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
- From the repository root, run `bash -n database/bots/import.sh`. Use a disposable database for an import smoke test.

