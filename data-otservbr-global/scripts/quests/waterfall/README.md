# Waterfall

## Overview
Component package under `scripts/quests/waterfall` containing 1 files (`movements_waterfall.lua`..`movements_waterfall.lua`).

## Interface
- `waterfall.onStepIn(creature, item, position, fromPosition)` [movements_waterfall.lua:waterfall.onStepIn]
- `MoveEvent()` assigned to `waterfall` [movements_waterfall.lua:waterfall]
- `MoveEvent()` registration [movements_waterfall.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_waterfall.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_waterfall.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_waterfall.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
