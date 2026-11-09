# Quests

## Overview
Intermediate blueprint grouping 1 subdirectories under `lib/core/quests`.

## Subdirectories & Boundaries
- [catalog](./catalog/README.md) - Component package under `lib/core/quests/catalog` containing 52 files (`001_the_queen_of_the_banshees.lua`..`init.lua`).

## Interface
- Defines 52 script/configuration files (`001_the_queen_of_the_banshees.lua` through `init.lua`) [001_the_queen_of_the_banshees.lua]
- Lua script module `001_the_queen_of_the_banshees.lua` [001_the_queen_of_the_banshees.lua:module]
- [catalog](./catalog/README.md) - Component package under `lib/core/quests/catalog` containing 52 files (`001_the_queen_of_the_banshees.lua`..`init.lua`).

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [003_spike_task.lua:getStorageValue]

## Side Effects
- Loads and executes `CORE_DIRECTORY .. "/lib/core/quests/catalog.lua"` via `dofile` [init.lua:dofile]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
