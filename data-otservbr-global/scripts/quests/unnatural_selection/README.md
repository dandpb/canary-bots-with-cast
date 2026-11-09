# Unnatural Selection

## Overview
Component package under `scripts/quests/unnatural_selection` containing 3 files (`actions_mission5_ray_of_light.lua`..`movements_mission3_dance_dance_evolution.lua`).

## Interface
- `unnatural.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission5_ray_of_light.lua:unnatural.onUse]
- `Action()` assigned to `unnatural` [actions_mission5_ray_of_light.lua:unnatural]
- `Action()` registration [actions_mission5_ray_of_light.lua:Action]
- `mission2AllAroundTheWorld.onStepIn(creature, item, position, fromPosition)` [movements_mission2_all_around_the_world.lua:mission2AllAroundTheWorld.onStepIn]
- `MoveEvent()` assigned to `mission2AllAroundTheWorld` [movements_mission2_all_around_the_world.lua:mission2AllAroundTheWorld]
- `MoveEvent()` registration [movements_mission2_all_around_the_world.lua:MoveEvent]
- `mission3DanceDanceEvolution.onStepIn(creature, item, position, fromPosition)` [movements_mission3_dance_dance_evolution.lua:mission3DanceDanceEvolution.onStepIn]
- `MoveEvent()` assigned to `mission3DanceDanceEvolution` [movements_mission3_dance_dance_evolution.lua:mission3DanceDanceEvolution]
- `MoveEvent()` registration [movements_mission3_dance_dance_evolution.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission5_ray_of_light.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_mission2_all_around_the_world.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_mission2_all_around_the_world.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_mission3_dance_dance_evolution.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_mission3_dance_dance_evolution.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission5_ray_of_light.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_mission5_ray_of_light.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_mission2_all_around_the_world.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_mission2_all_around_the_world.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_mission3_dance_dance_evolution.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_mission3_dance_dance_evolution.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
