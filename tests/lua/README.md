# Lua Regression Tests (`tests/lua`)

## Overview
Provides standalone Lua/LuaJIT tests for bot startup pacing and global saves, plus in-server tests for progression, combat and persistence.

## Interface
- `[bot_startup_test.lua]` — Exercises the real `BotStartup` handler (`data/scripts/globalevents/bot_manager.lua`) against a mock dispatcher and DB, verifying 997-bot loading, adaptive `100..1000 ms` backoff/recovery, 3-attempt retries, 50-bot visibility batches, and finalization scheduling.
- `[bot_persistence_no_xp_test.lua]` / `[bot_population_persistence_test.lua]` / `[bot_progression_test.lua]` / `[bot_progression_combat_test.lua]` / `[bot_progression_lifecycle_test.lua]` / `[global_server_save_test.lua]` — Regression suites covering bot progression, persistence, and server save hooks.
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
