# Demon Helmet

## Overview
Component package under `scripts/quests/demon_helmet` containing 2 files (`action-lever.lua`..`movement-walls.lua`).

## Interface
- `lever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-lever.lua:lever.onUse]
- `Action()` assigned to `lever` [action-lever.lua:lever]
- `Action()` registration [action-lever.lua:Action]
- `walls.onStepIn(creature, item, position, fromPosition)` [movement-walls.lua:walls.onStepIn]
- `walls.onStepOut(creature, item, position, fromPosition)` [movement-walls.lua:walls.onStepOut]
- `MoveEvent()` assigned to `walls` [movement-walls.lua:walls]
- `MoveEvent()` registration [movement-walls.lua:MoveEvent]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action-lever.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-walls.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movement-walls.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [action-lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action-lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement-walls.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [movement-walls.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [movement-walls.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
