# Hidden Threats

## Overview
Component package under `scripts/quests/hidden_threats` containing 4 files (`action-corym_works_doors.lua`..`movement-chests_check.lua`).

## Interface
- `perfectlyForgedKey.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-corym_works_doors.lua:perfectlyForgedKey.onUse]
- `Action()` assigned to `perfectlyForgedKey` [action-corym_works_doors.lua:perfectlyForgedKey]
- `Action()` registration [action-corym_works_doors.lua:Action]
- `keyForge.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-key_forge.lua:keyForge.onUse]
- `Action()` assigned to `keyForge` [action-key_forge.lua:keyForge]
- `Action()` registration [action-key_forge.lua:Action]
- `caveSpiderRoom.onStepIn(creature, item, position, fromPosition)` [movement-cave_spider_room.lua:caveSpiderRoom.onStepIn]
- `MoveEvent()` assigned to `caveSpiderRoom` [movement-cave_spider_room.lua:caveSpiderRoom]
- `MoveEvent()` registration [movement-cave_spider_room.lua:MoveEvent]
- `corymChests.onStepOut(creature, item, position, fromPosition)` [movement-chests_check.lua:corymChests.onStepOut]
- `MoveEvent()` assigned to `corymChests` [movement-chests_check.lua:corymChests]
- `MoveEvent()` registration [movement-chests_check.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action-corym_works_doors.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement-cave_spider_room.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-cave_spider_room.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement-chests_check.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-chests_check.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-corym_works_doors.lua:register]
- Mutates player or global storage state via `setStorageValue` [action-corym_works_doors.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-key_forge.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action-key_forge.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement-cave_spider_room.lua:register]
- Mutates player or global storage state via `setStorageValue` [movement-cave_spider_room.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [movement-cave_spider_room.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [movement-cave_spider_room.lua:teleportTo]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [movement-cave_spider_room.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement-chests_check.lua:register]
- Mutates player or global storage state via `setStorageValue` [movement-chests_check.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
