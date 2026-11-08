# Tinder Box Quest Chyllfroest

## Overview
Component package under `scripts/quests/tinder_box_quest_chyllfroest` containing 4 files (`actions_reward.lua`..`movements_prohibit_entry.lua`).

## Interface
- `tinderReward.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_reward.lua:tinderReward.onUse]
- `Action()` assigned to `tinderReward` [actions_reward.lua:tinderReward]
- `Action()` registration [actions_reward.lua:Action]
- `tinderBox.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_tinder_box.lua:tinderBox.onUse]
- `Action()` assigned to `tinderBox` [actions_tinder_box.lua:tinderBox]
- `Action()` registration [actions_tinder_box.lua:Action]
- `revertIce(toPosition)` [actions_ursagrodon.lua:revertIce]
- `ursagrodon.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ursagrodon.lua:ursagrodon.onUse]
- `Action()` assigned to `ursagrodon` [actions_ursagrodon.lua:ursagrodon]
- `Action()` registration [actions_ursagrodon.lua:Action]
- `movements_prohibit_entry.onStepIn(creature, item, position, fromPosition)` [movements_prohibit_entry.lua:movements_prohibit_entry.onStepIn]
- `MoveEvent()` assigned to `movements_prohibit_entry` [movements_prohibit_entry.lua:movements_prohibit_entry]
- `MoveEvent()` registration [movements_prohibit_entry.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_reward.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ursagrodon.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_ursagrodon.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_prohibit_entry.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_reward.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_reward.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_reward.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_tinder_box.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_tinder_box.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ursagrodon.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_ursagrodon.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_ursagrodon.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_ursagrodon.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_prohibit_entry.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_prohibit_entry.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
