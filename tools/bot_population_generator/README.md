# Bot Population Generator (`tools/bot_population_generator`)

## Overview
Generates deterministic MySQL population seed scripts, in-place level redistribution migrations, and drift-safe character rename migrations for the 997 simulated bot players under account `65000`.

## Interface
- `[generate.py:TOTAL_BOTS]` (`997`), `[generate.py:BOT_ACCOUNT_ID]` (`65000`), `[generate.py:BOT_ID_START]` (`65001`), `[generate.py:RESERVED_IDS]`, `[generate.py:TOWN_IDS]`, `[generate.py:LEVEL_TIERS]`.
- `[generate.py:PSTRG_OUTFITS_RANGE_START]` (`10001000`), `[generate.py:PSTRG_OUTFITS_RANGE_SIZE]` (`500`), `[generate.py:PSTRG_MOUNTS_RANGE_START]` (`10002001`), `[generate.py:PSTRG_MOUNTS_RANGE_SIZE]` (`10`), `[generate.py:PSTRG_MOUNTS_CURRENTMOUNT]` (`10002011`).
- `[generate.py:load_npc_names]`, `[generate.py:build_trigram_table]`, `[generate.py:generate_name]`, `[generate.py:generate_unique_names]` — Character-level trigram Markov name generator seeded from `otservbr-npc.xml` and legacy name pools.
- `[generate.py:level_for_index]`, `[generate.py:build_voc_assignment]`, `[generate.py:build_town_assignment]`, `[generate.py:vocation_id]`, `[generate.py:health_mana_cap]`, `[generate.py:experience_for_level]`, `[generate.py:skills_for_vocation]` — Deterministic bot stat, vocation, and town assignment helpers.
- `[generate.py:load_outfit_catalog]`, `[generate.py:load_mount_ids]`, `[generate.py:mount_ownership_bitmask_rows]`, `[generate.py:outfit_ownership_rows]` — XML catalog parsers and `player_storage` bitmask/packed-value encoders.
- `[generate.py:emit_sql]`, `[generate.py:read_id_vocation_csv]`, `[generate.py:emit_level_update_sql]`, `[generate.py:main]` — CLI entry point supporting `--npc-xml`, `--outfits-xml`, `--mounts-xml`, `--out`, `--seed`, and `--emit-update`.
- `[generate_rename_sql.py:sql_str]`, `[generate_rename_sql.py:main]` — Reads `bot_roster_updated.tsv` and emits `database/bots/19_bot_rename.sql` and `database/bots/19_bot_rename_rollback.sql`.
- SQL artifacts: `[bot_population_setup.sql:accounts]`, `[bot_population_setup.sql:players]`, `[bot_population_setup.sql:player_storage]`, `[bot_population_setup.sql:bot_state_persistence]`, `[bot_population_setup.sql:bot_commands]`, `[bot_level_redistribution.sql:players]`.

## Invariants
- `[generate.py:TOTAL_BOTS]` is fixed at prime `997` with Fisher-Yates pre-shuffled vocation (`[generate.py:build_voc_assignment]`) and town (`[generate.py:build_town_assignment]`) sequences so stratified stride picking never aliases periodic assignments.
- `[generate.py:RESERVED_IDS]` (`{65201..65207}`) must be skipped when allocating bot player IDs starting at `65001` to avoid colliding with non-bot characters.
- `[generate.py:LEVEL_TIERS]` index-to-level bands must remain synchronized with forge-tier bands in `bot_engine.cpp::applyBotForgeTiers`.
- `[generate_rename_sql.py:main]` asserts that the 997 post-migration names contain zero case-insensitive duplicates, zero collisions with `REAL_PLAYERS`, and zero overlap between newly assigned names and retained original names (where `new_name` contains digits).
- `[generate_rename_sql.py:main]` requires the Canary server to be stopped when applying rename SQL because `iologindata_save_player.cpp` overwrites `players.name` on save.

## Side Effects
- `[generate.py:emit_sql]` and `[generate.py:emit_level_update_sql]` write SQL migration files to `--out` (such as `bot_population_setup.sql` or `bot_level_redistribution.sql`).
- Executing `bot_population_setup.sql` against MySQL upserts account `65000` into `accounts`, deletes all `players` with `account_id = 65000`, truncates `bot_state_persistence` and `bot_commands`, and bulk-inserts 997 `players` rows plus `player_storage` outfit and mount unlock rows.
- Executing `bot_level_redistribution.sql` performs an in-place transactional `UPDATE` on `players` (`level`, `vocation`, `health`, `healthmax`, `mana`, `manamax`, `experience`, `cap`) for `account_id = 65000`.
- `[generate_rename_sql.py:main]` writes `database/bots/19_bot_rename.sql` and `database/bots/19_bot_rename_rollback.sql`.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
