# Others

## Overview
Component package under `startup/others` containing 2 files (`functions.lua`..`load.lua`).

## Interface
- `CreateMapItem(tablename)` [functions.lua:CreateMapItem]
- `loadLuaMapAction(tablename)` [functions.lua:loadLuaMapAction]
- `loadLuaMapUnique(tablename)` [functions.lua:loadLuaMapUnique]
- `loadLuaMapSign(tablename)` [functions.lua:loadLuaMapSign]
- `loadLuaMapBookDocument(tablename)` [functions.lua:loadLuaMapBookDocument]
- `updateKeysStorage(tablename)` [functions.lua:updateKeysStorage]
- `dofile(DATA_DIRECTORY .. "/startup/others/functions.lua")` module loader [load.lua:dofile]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [functions.lua:Tile]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [functions.lua:db.query]

## Side Effects
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [functions.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [functions.lua:transform]
- Executes SQL DDL/DML statements against the database via `db.query` [functions.lua:db.query]
- Loads and executes `DATA_DIRECTORY .. "/startup/others/functions.lua"` via `dofile` [load.lua:dofile]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
