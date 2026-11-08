# The Shattered Isles Quest

## Overview
Component package under `scripts/quests/the_shattered_isles_quest` containing 4 files (`action_nargor_maps.lua`..`movement_teleport.lua`).

## Interface
- `nargorMaps.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_nargor_maps.lua:nargorMaps.onUse]
- `Action()` assigned to `nargorMaps` [action_nargor_maps.lua:nargorMaps]
- `Action()` registration [action_nargor_maps.lua:Action]
- `tortoiseEggNargor.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_tortoise_egg_nargor.lua:tortoiseEggNargor.onUse]
- `Action()` assigned to `tortoiseEggNargor` [action_tortoise_egg_nargor.lua:tortoiseEggNargor]
- `Action()` registration [action_tortoise_egg_nargor.lua:Action]
- `energyBarrier.onStepIn(creature, item, position, fromPosition)` [movement_energy_barrier.lua:energyBarrier.onStepIn]
- `MoveEvent()` assigned to `energyBarrier` [movement_energy_barrier.lua:energyBarrier]
- `MoveEvent()` registration [movement_energy_barrier.lua:MoveEvent]
- `teleport.onStepIn(creature, item, position, fromPosition)` [movement_teleport.lua:teleport.onStepIn]
- `MoveEvent()` assigned to `teleport` [movement_teleport.lua:teleport]
- `MoveEvent()` registration [movement_teleport.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_nargor_maps.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_tortoise_egg_nargor.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement_energy_barrier.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_energy_barrier.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_teleport.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movement_teleport.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_nargor_maps.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_nargor_maps.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_tortoise_egg_nargor.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_tortoise_egg_nargor.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_tortoise_egg_nargor.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement_energy_barrier.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movement_energy_barrier.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement_teleport.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movement_teleport.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [movement_teleport.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
