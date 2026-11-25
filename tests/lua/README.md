# Lua Regression Tests (`tests/lua`)

## Overview
Provides standalone Lua/LuaJIT tests for bot startup pacing and global saves, plus in-server tests for progression, combat and persistence.

## Interface
- `[bot_startup_test.lua]` / `[test_bot_startup.lua]` — Exercises the real `BotStartup` handler (`data/scripts/globalevents/bot_manager.lua`) against a mock dispatcher and DB, verifying 997-bot loading, adaptive `100..1000 ms` backoff/recovery, 3-attempt retries, 50-bot visibility batches, and finalization scheduling.
- `[bot_persistence_no_xp_test.lua]` / `[bot_population_persistence_test.lua]` / `[bot_progression_test.lua]` / `[bot_progression_combat_test.lua]` / `[bot_progression_lifecycle_test.lua]` / `[bot_house_reclaim_test.lua]` / `[global_server_save_test.lua]` — Regression suites covering bot progression, persistence, house reclaim, and server save hooks.
- GameStore, Bank, Taskboard & NPC standalone regressions: `bank_transfer_outcome_test.lua`, `gamestore_coin_payment_test.lua`, `gamestore_configured_purchase_test.lua`, `gamestore_fulfillment_test.lua`, `gamestore_order_test.lua`, `gamestore_purchase_routing_test.lua`, `gamestore_transfer_test.lua`, `hireling_persistence_test.lua`, `test_advance_save_debounce.lua`, `test_bank_command_amounts.lua`, `test_encounter_auto_advance.lua`, `test_gamestore_bootstrap.lua`, `test_gamestore_consumable_deliveries.lua`, `test_gamestore_cosmetic_deliveries.lua`, `test_gamestore_furniture_deliveries.lua`, `test_gamestore_taskboard_expansion.lua`, `test_npc_messaging.lua`, `test_primal_pod_position.lua`, `test_soul_war_hatred_targets.lua`, `test_starter_spell_identities.lua`, `test_table_serialization.lua`, `test_taskboard_module.lua`, `test_taskboard_store_summary_wire.lua`, `test_wyrdin_keywords.lua`, and `bench_table_serialization.lua`.
- Acceptance notes & evidence: [`README.bot-progression.md`](./README.bot-progression.md), [`LIFECYCLE_ACCEPTANCE.md`](./LIFECYCLE_ACCEPTANCE.md), [`INTEGRATION_UPDATE_2026-11-05.md`](./INTEGRATION_UPDATE_2026-11-05.md), [`RELOAD_PROGRESS_ACCEPTANCE.md`](./RELOAD_PROGRESS_ACCEPTANCE.md), [`RELOAD_QUEST_ACCEPTANCE.md`](./RELOAD_QUEST_ACCEPTANCE.md), `*.json`.

## Invariants
- The startup and global-save tests use fake dispatcher/database adapters and run from the repository root with Lua or LuaJIT. The progression and persistence scripts use Canary's Lua runtime, including native `Player` objects. The no-XP persistence check also loads the QA lifecycle bridge.

## Side Effects
- The standalone tests exercise in-memory stubs. The in-server suites exercise player and database state in an isolated QA fixture.

## Verification

```sh
lua tests/lua/bot_startup_test.lua
lua tests/lua/global_server_save_test.lua
lua tools/bot_brain/test_startup_batches.lua
```

Use [the progression guide](README.bot-progression.md) for the in-server suites.
