# Krailos

## Overview
Component package under `scripts/quests/krailos` containing 1 files (`movements_access_depot.lua`..`movements_access_depot.lua`).

## Interface
- `accessDepot.onStepIn(creature, item, position, fromPosition)` [movements_access_depot.lua:accessDepot.onStepIn]
- `MoveEvent()` assigned to `accessDepot` [movements_access_depot.lua:accessDepot]
- `MoveEvent()` registration [movements_access_depot.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_access_depot.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_access_depot.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_access_depot.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
