# Parchment Room

## Overview
Component package under `scripts/quests/parchment_room` containing 1 files (`parchment.lua`..`parchment.lua`).

## Interface
- `recreateParchment(position)` [parchment.lua:recreateParchment]
- `parchment.onRemoveItem(item, position)` [parchment.lua:parchment.onRemoveItem]
- `MoveEvent()` assigned to `parchment` [parchment.lua:parchment]
- `MoveEvent()` registration [parchment.lua:MoveEvent]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [parchment.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [parchment.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [parchment.lua:Game]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [parchment.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
