# The Queen Of The Banshees

## Overview
Component package under `scripts/quests/the_queen_of_the_banshees` containing 16 files (`action-1-first_seal_lever.lua`..`movement-7-last_seal_flame.lua`).

## Interface
- `leverFirstSeal.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-1-first_seal_lever.lua:leverFirstSeal.onUse]
- `Action()` assigned to `leverFirstSeal` [action-1-first_seal_lever.lua:leverFirstSeal]
- `Action()` registration [action-1-first_seal_lever.lua:Action]
- `thirdSealLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-3-third_seal_lever.lua:thirdSealLever.onUse]
- `Action()` assigned to `thirdSealLever` [action-3-third_seal_lever.lua:thirdSealLever]
- `Action()` registration [action-3-third_seal_lever.lua:Action]
- `sixthSeal.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-6-sixth_seal_lever.lua:sixthSeal.onUse]
- `Action()` assigned to `sixthSeal` [action-6-sixth_seal_lever.lua:sixthSeal]
- `Action()` registration [action-6-sixth_seal_lever.lua:Action]
- `firstSealCloseMw.onStepIn(creature, item, position, fromPosition)` [movement-1-first_seal_close_mw.lua:firstSealCloseMw.onStepIn]
- `MoveEvent()` assigned to `firstSealCloseMw` [movement-1-first_seal_close_mw.lua:firstSealCloseMw]
- `MoveEvent()` registration [movement-1-first_seal_close_mw.lua:MoveEvent]
- `firstSealFlame.onStepIn(creature, item, position, fromPosition)` [movement-1-first_seal_flame.lua:firstSealFlame.onStepIn]
- `MoveEvent()` assigned to `firstSealFlame` [movement-1-first_seal_flame.lua:firstSealFlame]
- `MoveEvent()` registration [movement-1-first_seal_flame.lua:MoveEvent]
- `teleportBack.onStepIn(creature, item, position, fromPosition)` [movement-1-first_seal_teleport_back.lua:teleportBack.onStepIn]
- `MoveEvent()` assigned to `teleportBack` [movement-1-first_seal_teleport_back.lua:teleportBack]
- `MoveEvent()` registration [movement-1-first_seal_teleport_back.lua:MoveEvent]
- `secondSealFlame.onStepIn(creature, item, position, fromPosition)` [movement-2-second_seal_flame.lua:secondSealFlame.onStepIn]
- `MoveEvent()` assigned to `secondSealFlame` [movement-2-second_seal_flame.lua:secondSealFlame]
- `MoveEvent()` registration [movement-2-second_seal_flame.lua:MoveEvent]
- `secondSealPearl.onStepIn(creature, item, position, fromPosition)` [movement-2-second_seal_pearl.lua:secondSealPearl.onStepIn]
- `MoveEvent()` assigned to `secondSealPearl` [movement-2-second_seal_pearl.lua:secondSealPearl]
- `MoveEvent()` registration [movement-2-second_seal_pearl.lua:MoveEvent]
- `thirdSealFlame.onStepIn(creature, item, position, fromPosition)` [movement-3-third_seal_flame.lua:thirdSealFlame.onStepIn]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action-3-third_seal_lever.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action-6-sixth_seal_lever.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-1-first_seal_close_mw.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement-1-first_seal_flame.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-1-first_seal_flame.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-1-first_seal_teleport_back.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement-2-second_seal_flame.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-2-second_seal_flame.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement-2-second_seal_pearl.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-2-second_seal_pearl.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movement-2-second_seal_pearl.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement-3-third_seal_flame.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-1-first_seal_lever.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action-1-first_seal_lever.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [action-1-first_seal_lever.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-3-third_seal_lever.lua:register]
- Mutates player or global storage state via `setStorageValue` [action-3-third_seal_lever.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action-3-third_seal_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-6-sixth_seal_lever.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action-6-sixth_seal_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement-1-first_seal_close_mw.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [movement-1-first_seal_close_mw.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement-1-first_seal_flame.lua:register]
- Mutates player or global storage state via `setStorageValue` [movement-1-first_seal_flame.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
