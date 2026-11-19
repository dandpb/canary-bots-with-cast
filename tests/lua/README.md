# Lua Regression Tests (`tests/lua`)

## Overview
Provides standalone Lua/LuaJIT regression tests validating bot startup pacing, quest-access ordering, XP progression, hibernation/reload persistence, and global server saves without requiring a compiled C++ server or live database.

## Interface
- `[bot_startup_test.lua]` — Exercises the real `BotStartup` handler (`data/scripts/globalevents/bot_manager.lua`) against a mock dispatcher and DB, verifying 997-bot loading, adaptive `100..1000 ms` backoff/recovery, 3-attempt retries, 50-bot visibility batches, and finalization scheduling.
- `[bot_persistence_no_xp_test.lua]` / `[bot_population_persistence_test.lua]` / `[bot_progression_test.lua]` / `[bot_progression_combat_test.lua]` / `[bot_progression_lifecycle_test.lua]` / `[global_server_save_test.lua]` — Regression suites covering bot progression, persistence, and server save hooks.
- Acceptance notes & evidence: [`README.bot-progression.md`](./README.bot-progression.md), [`LIFECYCLE_ACCEPTANCE.md`](./LIFECYCLE_ACCEPTANCE.md), [`INTEGRATION_UPDATE_2026-11-05.md`](./INTEGRATION_UPDATE_2026-11-05.md), [`RELOAD_PROGRESS_ACCEPTANCE.md`](./RELOAD_PROGRESS_ACCEPTANCE.md), [`RELOAD_QUEST_ACCEPTANCE.md`](./RELOAD_QUEST_ACCEPTANCE.md), `*.json`.

## Invariants
- Tests execute deterministically from the repository root under both `lua` and `luajit` with zero external network or MySQL dependencies.

## Side Effects
- None (in-memory fake dispatcher and database stubs).

## Verification
- Run: `lua tests/lua/bot_startup_test.lua`
