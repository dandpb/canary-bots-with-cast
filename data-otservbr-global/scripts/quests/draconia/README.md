# Draconia

## Overview
Component package under `scripts/quests/draconia` containing 3 files (`action-lever.lua`..`movement-exit_teleport.lua`).

## Interface
- `lever1.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-lever.lua:lever1.onUse]
- `lever2.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-lever.lua:lever2.onUse]
- `Action()` assigned to `lever1` [action-lever.lua:lever1]
- `Action()` assigned to `lever2` [action-lever.lua:lever2]
- `Action()` registration [action-lever.lua:Action]
- `escape.onStepIn(creature, item, position, fromPosition)` [movement-escape.lua:escape.onStepIn]
- `MoveEvent()` assigned to `escape` [movement-escape.lua:escape]
- `MoveEvent()` registration [movement-escape.lua:MoveEvent]
- `exitTeleport.onStepIn(creature, item, position, fromPosition)` [movement-exit_teleport.lua:exitTeleport.onStepIn]
- `MoveEvent()` assigned to `exitTeleport` [movement-exit_teleport.lua:exitTeleport]
- `MoveEvent()` registration [movement-exit_teleport.lua:MoveEvent]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action-lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement-escape.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-escape.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movement-escape.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-exit_teleport.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movement-exit_teleport.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [action-lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action-lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement-escape.lua:register]
- Mutates player or global storage state via `setStorageValue` [movement-escape.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [movement-escape.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [movement-escape.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement-exit_teleport.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movement-exit_teleport.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
