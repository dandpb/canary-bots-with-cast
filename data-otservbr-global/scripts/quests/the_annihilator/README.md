# The Annihilator

## Overview
Component package under `scripts/quests/the_annihilator` containing 2 files (`door.lua`..`lever.lua`).

## Interface
- `door.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [door.lua:door.onUse]
- `Action()` assigned to `door` [door.lua:door]
- `Action()` registration [door.lua:Action]
- `lever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [lever.lua:lever.onUse]
- `Action()` assigned to `lever` [lever.lua:lever]
- `Action()` registration [lever.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [door.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [lever.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [door.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [door.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [door.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [lever.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [lever.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [lever.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
