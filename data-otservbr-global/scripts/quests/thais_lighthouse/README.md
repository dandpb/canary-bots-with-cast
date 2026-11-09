# Thais Lighthouse

## Overview
Component package under `scripts/quests/thais_lighthouse` containing 2 files (`action-lever.lua`..`movement-stair.lua`).

## Interface
- `lever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-lever.lua:lever.onUse]
- `Action()` assigned to `lever` [action-lever.lua:lever]
- `Action()` registration [action-lever.lua:Action]
- `stair.onStepIn(creature, item, position, fromPosition)` [movement-stair.lua:stair.onStepIn]
- `stair.onStepOut(creature, item, position, fromPosition)` [movement-stair.lua:stair.onStepOut]
- `MoveEvent()` assigned to `stair` [movement-stair.lua:stair]
- `MoveEvent()` registration [movement-stair.lua:MoveEvent]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action-lever.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movement-stair.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [action-lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action-lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement-stair.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [movement-stair.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
