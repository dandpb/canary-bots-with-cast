# Tables

## Overview
Component package under `lib/tables` containing 3 files (`load.lua`..`town.lua`).

## Interface
- `dofile(DATA_DIRECTORY .. "/lib/tables/teleport_item_destinations.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/lib/tables/town.lua")` module loader [load.lua:dofile]
- Global symbol `ItemTeleports` [teleport_item_destinations.lua:ItemTeleports]
- Global symbol `TOWNS_LIST` [town.lua:TOWNS_LIST]

## Invariants
- None

## Side Effects
- Loads and executes `DATA_DIRECTORY .. "/lib/tables/teleport_item_destinations.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/lib/tables/town.lua"` via `dofile` [load.lua:dofile]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
