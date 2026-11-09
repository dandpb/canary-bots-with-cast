# The Hunt For The Sea Serpent

## Overview
Component package under `scripts/quests/the_hunt_for_the_sea_serpent` containing 2 files (`actions_bait.lua`..`movements_teleports.lua`).

## Interface
- `bait.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bait.lua:bait.onUse]
- `telescope.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bait.lua:telescope.onUse]
- `Action()` assigned to `bait` [actions_bait.lua:bait]
- `Action()` assigned to `telescope` [actions_bait.lua:telescope]
- `Action()` registration [actions_bait.lua:Action]
- `teleports.onStepIn(creature, item, position, fromPosition)` [movements_teleports.lua:teleports.onStepIn]
- `MoveEvent()` assigned to `teleports` [movements_teleports.lua:teleports]
- `MoveEvent()` registration [movements_teleports.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_bait.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_teleports.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_teleports.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bait.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_bait.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bait.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_teleports.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_teleports.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
