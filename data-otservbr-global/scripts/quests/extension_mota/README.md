# Extension Mota

## Overview
Component package under `scripts/quests/extension_mota` containing 1 files (`movements_extension_mota.lua`..`movements_extension_mota.lua`).

## Interface
- `extensionMota.onStepIn(creature, item, position, fromPosition)` [movements_extension_mota.lua:extensionMota.onStepIn]
- `MoveEvent()` assigned to `extensionMota` [movements_extension_mota.lua:extensionMota]
- `MoveEvent()` registration [movements_extension_mota.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_extension_mota.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_extension_mota.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_extension_mota.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
