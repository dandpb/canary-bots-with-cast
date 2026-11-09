# Rookgaard

## Overview
Component package under `scripts/movements/rookgaard` containing 3 files (`level_bridge.lua`..`rook_village.lua`).

## Interface
- `levelBridge.onStepIn(creature, item, position, fromPosition)` [level_bridge.lua:levelBridge.onStepIn]
- `MoveEvent()` assigned to `levelBridge` [level_bridge.lua:levelBridge]
- `MoveEvent()` registration [level_bridge.lua:MoveEvent]
- `premiumBridge.onStepIn(creature, item, position, fromPosition)` [premium_bridge.lua:premiumBridge.onStepIn]
- `MoveEvent()` assigned to `premiumBridge` [premium_bridge.lua:premiumBridge]
- `MoveEvent()` registration [premium_bridge.lua:MoveEvent]
- `rookVillage.onStepIn(creature, item, position, fromPosition)` [rook_village.lua:rookVillage.onStepIn]
- `MoveEvent()` assigned to `rookVillage` [rook_village.lua:rookVillage]
- `MoveEvent()` registration [rook_village.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [level_bridge.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [premium_bridge.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [rook_village.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [level_bridge.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [level_bridge.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [premium_bridge.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [premium_bridge.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [rook_village.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [rook_village.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
