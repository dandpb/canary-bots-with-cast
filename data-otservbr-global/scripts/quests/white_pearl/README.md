# White Pearl

## Overview
Component package under `scripts/quests/white_pearl` containing 1 files (`movements_white_pearl.lua`..`movements_white_pearl.lua`).

## Interface
- `whitePearl.onStepIn(creature, item, position, fromPosition)` [movements_white_pearl.lua:whitePearl.onStepIn]
- `MoveEvent()` assigned to `whitePearl` [movements_white_pearl.lua:whitePearl]
- `MoveEvent()` registration [movements_white_pearl.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_white_pearl.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movements_white_pearl.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_white_pearl.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_white_pearl.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
