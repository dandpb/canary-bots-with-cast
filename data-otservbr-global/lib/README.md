# Lib

## Overview
Provides 1 direct files (`lib.lua`..`lib.lua`) and 5 subdirectories under `lib`.

## Interface
- `dofile(DATA_DIRECTORY .. "/lib/core/load.lua")` module loader [lib.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/lib/others/load.lua")` module loader [lib.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/lib/quests/quest.lua")` module loader [lib.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/lib/tables/load.lua")` module loader [lib.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/lib/functions/load.lua")` module loader [lib.lua:dofile]
- [core](./core/README.md) - Provides 4 direct files (`constants.lua`..`storages.lua`) and 1 subdirectories under `lib/core`.
- [functions](./functions/README.md) - Component package under `lib/functions` containing 2 files (`load.lua`..`players.lua`).
- [others](./others/README.md) - Component package under `lib/others` containing 3 files (`dawnport.lua`..`soulpit.lua`).
- [quests](./quests/README.md) - Component package under `lib/quests` containing 11 files (`bigfoot_burden.lua`..`their_masters_voice.lua`).
- [tables](./tables/README.md) - Component package under `lib/tables` containing 3 files (`load.lua`..`town.lua`).

## Invariants
- None

## Side Effects
- Loads and executes `DATA_DIRECTORY .. "/lib/core/load.lua"` via `dofile` [lib.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/lib/others/load.lua"` via `dofile` [lib.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/lib/quests/quest.lua"` via `dofile` [lib.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/lib/tables/load.lua"` via `dofile` [lib.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/lib/functions/load.lua"` via `dofile` [lib.lua:dofile]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
