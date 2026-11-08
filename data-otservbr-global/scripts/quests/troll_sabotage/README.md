# Troll Sabotage

## Overview
Component package under `scripts/quests/troll_sabotage` containing 1 files (`movements_teleport.lua`..`movements_teleport.lua`).

## Interface
- `boots(player, item, fromPosition, position)` [movements_teleport.lua:boots]
- `helmet(player, item, fromPosition, position)` [movements_teleport.lua:helmet]
- `teleport.onStepIn(player, item, fromPosition, position, target)` [movements_teleport.lua:teleport.onStepIn]
- `MoveEvent()` assigned to `teleport` [movements_teleport.lua:teleport]
- `MoveEvent()` registration [movements_teleport.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_teleport.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_teleport.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_teleport.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_teleport.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
