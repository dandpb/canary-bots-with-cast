# Core

## Overview
Provides 4 direct files (`constants.lua`..`storages.lua`) and 1 subdirectories under `lib/core`.

## Interface
- Lua script module `constants.lua` [constants.lua:module]
- `dofile(DATA_DIRECTORY .. "/lib/core/storages.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/lib/core/constants.lua")` module loader [load.lua:dofile]
- `require("data-otservbr-global.lib.core.quests")` module loader [load.lua:require]
- `require("data.lib.core.quests.loader")` module loader [quests.lua:require]
- Global symbol `Storage` [storages.lua:Storage]
- Global symbol `GlobalStorage` [storages.lua:GlobalStorage]
- [quests](./quests/README.md) - Intermediate blueprint grouping 1 subdirectories under `lib/core/quests`.

## Invariants
- None

## Side Effects
- Loads and executes `DATA_DIRECTORY .. "/lib/core/storages.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/lib/core/constants.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `"data-otservbr-global.lib.core.quests"` via `require` [load.lua:require]
- Loads and executes `"data.lib.core.quests.loader"` via `require` [quests.lua:require]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
