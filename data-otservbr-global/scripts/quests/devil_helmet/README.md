# Devil Helmet

## Overview
Component package under `scripts/quests/devil_helmet` containing 1 files (`movements_sewer.lua`..`movements_sewer.lua`).

## Interface
- `sewer.onStepIn(creature, item, position, fromPosition)` [movements_sewer.lua:sewer.onStepIn]
- `sewer.onStepOut(creature, item, position, fromPosition)` [movements_sewer.lua:sewer.onStepOut]
- `MoveEvent()` assigned to `sewer` [movements_sewer.lua:sewer]
- `MoveEvent()` registration [movements_sewer.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_sewer.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movements_sewer.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_sewer.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [movements_sewer.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [movements_sewer.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
