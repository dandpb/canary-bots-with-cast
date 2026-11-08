# Chayenne Realm

## Overview
Component package under `scripts/quests/chayenne_realm` containing 3 files (`actions_lever.lua`..`movements_enter_realm.lua`).

## Interface
- `chayenneLever.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_lever.lua:chayenneLever.onUse]
- `Action()` assigned to `chayenneLever` [actions_lever.lua:chayenneLever]
- `Action()` registration [actions_lever.lua:Action]
- `chayenneReward.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_reward.lua:chayenneReward.onUse]
- `Action()` assigned to `chayenneReward` [actions_reward.lua:chayenneReward]
- `Action()` registration [actions_reward.lua:Action]
- `enterRealm.onStepIn(creature, item, position, fromPosition)` [movements_enter_realm.lua:enterRealm.onStepIn]
- `MoveEvent()` assigned to `enterRealm` [movements_enter_realm.lua:enterRealm]
- `MoveEvent()` registration [movements_enter_realm.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lever.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_reward.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_enter_realm.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lever.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_lever.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_lever.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_lever.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_reward.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_reward.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_reward.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_enter_realm.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_enter_realm.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
