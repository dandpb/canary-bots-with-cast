# Bursting At The Seams Museum

## Overview
Component package under `scripts/quests/the_secret_library_quest/bursting_at_the_seams_museum` containing 6 files (`actions_bony_rod.lua`..`movements_teleportTo.lua`).

## Interface
- `actions_museum_bony_rod.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bony_rod.lua:actions_museum_bony_rod.onUse]
- `Action()` assigned to `actions_museum_bony_rod` [actions_bony_rod.lua:actions_museum_bony_rod]
- `Action()` registration [actions_bony_rod.lua:Action]
- `actions_museum_doors.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_doors.lua:actions_museum_doors.onUse]
- `Action()` assigned to `actions_museum_doors` [actions_doors.lua:actions_museum_doors]
- `Action()` registration [actions_doors.lua:Action]
- `actions_museum_gems.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_gems.lua:actions_museum_gems.onUse]
- `Action()` assigned to `actions_museum_gems` [actions_gems.lua:actions_museum_gems]
- `Action()` registration [actions_gems.lua:Action]
- `actions_museum_levers.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_levers.lua:actions_museum_levers.onUse]
- `Action()` assigned to `actions_museum_levers` [actions_levers.lua:actions_museum_levers]
- `Action()` registration [actions_levers.lua:Action]
- `actions_museum_sample_blood.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_sample_blood.lua:actions_museum_sample_blood.onUse]
- `Action()` assigned to `actions_museum_sample_blood` [actions_sample_blood.lua:actions_museum_sample_blood]
- `Action()` registration [actions_sample_blood.lua:Action]
- `sendFire(position)` [movements_teleportTo.lua:sendFire]
- `movements_museum_teleportTo.onStepIn(creature, item, position, fromPosition)` [movements_teleportTo.lua:movements_museum_teleportTo.onStepIn]
- `MoveEvent()` assigned to `movements_museum_teleportTo` [movements_teleportTo.lua:movements_museum_teleportTo]
- `MoveEvent()` registration [movements_teleportTo.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_bony_rod.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_doors.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_doors.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_gems.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_levers.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_sample_blood.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_teleportTo.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_teleportTo.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bony_rod.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_bony_rod.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bony_rod.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_doors.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_doors.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_doors.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_gems.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_gems.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_gems.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_levers.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_levers.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_levers.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
