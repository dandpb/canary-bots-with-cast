# Tables

## Overview
Component package under `startup/tables` containing 17 files (`chest.lua`..`writeable.lua`).

## Interface
- Global symbol `ChestAction` [chest.lua:ChestAction]
- Global symbol `ChestUnique` [chest.lua:ChestUnique]
- Global symbol `CorpseAction` [corpse.lua:CorpseAction]
- Global symbol `CorpseUnique` [corpse.lua:CorpseUnique]
- Global symbol `CreateItemOnMap` [create_item.lua:CreateItemOnMap]
- Global symbol `KeyDoorAction` [door_key.lua:KeyDoorAction]
- Global symbol `LevelDoorAction` [door_level.lua:LevelDoorAction]
- Global symbol `QuestDoorAction` [door_quest.lua:QuestDoorAction]
- Global symbol `QuestDoorUnique` [door_quest.lua:QuestDoorUnique]
- Global symbol `ItemAction` [item.lua:ItemAction]
- Global symbol `ItemUnique` [item.lua:ItemUnique]
- Global symbol `DailyRewardAction` [item_daily_reward.lua:DailyRewardAction]
- Global symbol `ItemUnmovableAction` [item_unmovable.lua:ItemUnmovableAction]
- Global symbol `LeverAction` [lever.lua:LeverAction]
- Global symbol `LeverUnique` [lever.lua:LeverUnique]
- `dofile(DATA_DIRECTORY .. "/startup/tables/chest.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/startup/tables/corpse.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/startup/tables/create_item.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/startup/tables/door_key.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/startup/tables/door_level.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/startup/tables/door_quest.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/startup/tables/item.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/startup/tables/item_daily_reward.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/startup/tables/item_unmovable.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/startup/tables/lever.lua")` module loader [load.lua:dofile]

## Invariants
- None

## Side Effects
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/chest.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/corpse.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/create_item.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/door_key.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/door_level.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/door_quest.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/item.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/item_daily_reward.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/item_unmovable.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/lever.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/teleport.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/teleport_item.lua"` via `dofile` [load.lua:dofile]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
