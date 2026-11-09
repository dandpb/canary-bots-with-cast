# The Paradox Tower

## Overview
Component package under `scripts/quests/the_paradox_tower` containing 11 files (`action_fifth_floor_lever.lua`..`trap_in_the_tree.lua`).

## Interface
- `fifthFloorLever.onUse(creature, item, position, fromPosition)` [action_fifth_floor_lever.lua:fifthFloorLever.onUse]
- `Action()` assigned to `fifthFloorLever` [action_fifth_floor_lever.lua:fifthFloorLever]
- `Action()` registration [action_fifth_floor_lever.lua:Action]
- `fourFloorLever.onUse(creature, item, position, fromPosition)` [action_four_floor_lever.lua:fourFloorLever.onUse]
- `Action()` assigned to `fourFloorLever` [action_four_floor_lever.lua:fourFloorLever]
- `Action()` registration [action_four_floor_lever.lua:Action]
- `secondFloorLever.onUse(creature, item, position, fromPosition)` [action_second_floor_lever.lua:secondFloorLever.onUse]
- `Action()` assigned to `secondFloorLever` [action_second_floor_lever.lua:secondFloorLever]
- `Action()` registration [action_second_floor_lever.lua:Action]
- `thirdFloorLever.onUse(creature, item, position, fromPosition)` [action_third_floor_lever.lua:thirdFloorLever.onUse]
- `Action()` assigned to `thirdFloorLever` [action_third_floor_lever.lua:thirdFloorLever]
- `Action()` registration [action_third_floor_lever.lua:Action]
- `teleportTileBack.onStepIn(creature, item, position, fromPosition)` [move_let_the _quest.lua:teleportTileBack.onStepIn]
- `MoveEvent()` assigned to `teleportTileBack` [move_let_the _quest.lua:teleportTileBack]
- `MoveEvent()` registration [move_let_the _quest.lua:MoveEvent]
- `firstFloorStair.onStepIn(creature, item, position, fromPosition)` [movement_first_floor_stair.lua:firstFloorStair.onStepIn]
- `MoveEvent()` assigned to `firstFloorStair` [movement_first_floor_stair.lua:firstFloorStair]
- `MoveEvent()` registration [movement_first_floor_stair.lua:MoveEvent]
- `lastFloorReward.onStepIn(creature, item, position, fromPosition)` [movement_last_floor_reward.lua:lastFloorReward.onStepIn]
- `MoveEvent()` assigned to `lastFloorReward` [movement_last_floor_reward.lua:lastFloorReward]
- `MoveEvent()` registration [movement_last_floor_reward.lua:MoveEvent]
- `sacrificeSkulls.onStepIn(creature, item, position, fromPosition)` [movement_sacrifice_skulls.lua:sacrificeSkulls.onStepIn]
- `MoveEvent()` assigned to `sacrificeSkulls` [movement_sacrifice_skulls.lua:sacrificeSkulls]
- `MoveEvent()` registration [movement_sacrifice_skulls.lua:MoveEvent]
- `teleportTile.onStepIn(creature, item, position, fromPosition)` [movement_strange_carvings_in _the_southeast.lua:teleportTile.onStepIn]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [action_fifth_floor_lever.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [action_four_floor_lever.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [action_second_floor_lever.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [action_third_floor_lever.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [move_let_the _quest.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_first_floor_stair.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement_last_floor_reward.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_last_floor_reward.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement_sacrifice_skulls.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_sacrifice_skulls.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movement_sacrifice_skulls.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_strange_carvings_in _the_southeast.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_fifth_floor_lever.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_fifth_floor_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_four_floor_lever.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_four_floor_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_second_floor_lever.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_second_floor_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_third_floor_lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [action_third_floor_lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_third_floor_lever.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [action_third_floor_lever.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [move_let_the _quest.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [move_let_the _quest.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
