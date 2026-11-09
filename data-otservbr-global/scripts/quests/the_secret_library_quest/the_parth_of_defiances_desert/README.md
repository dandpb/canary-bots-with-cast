# The Parth Of Defiances Desert

## Overview
Component package under `scripts/quests/the_secret_library_quest/the_parth_of_defiances_desert` containing 6 files (`actions_chests.lua`..`movements_teleportTo.lua`).

## Interface
- `actions_desert_chests.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_chests.lua:actions_desert_chests.onUse]
- `Action()` assigned to `actions_desert_chests` [actions_chests.lua:actions_desert_chests]
- `Action()` registration [actions_chests.lua:Action]
- `actions_desert_doors.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_doors.lua:actions_desert_doors.onUse]
- `Action()` assigned to `actions_desert_doors` [actions_doors.lua:actions_desert_doors]
- `Action()` registration [actions_doors.lua:Action]
- `isQuestComplete(cid)` [actions_totems.lua:isQuestComplete]
- `revert(old, new, position)` [actions_totems.lua:revert]
- `actions_desert_totems.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_totems.lua:actions_desert_totems.onUse]
- `Action()` assigned to `actions_desert_totems` [actions_totems.lua:actions_desert_totems]
- `Action()` registration [actions_totems.lua:Action]
- `movements_desert_color_puzzle.onStepIn(creature, item, position, fromPosition)` [movements_color_puzzle.lua:movements_desert_color_puzzle.onStepIn]
- `MoveEvent()` assigned to `movements_desert_color_puzzle` [movements_color_puzzle.lua:movements_desert_color_puzzle]
- `MoveEvent()` registration [movements_color_puzzle.lua:MoveEvent]
- `isFood(itemid)` [movements_sacrifice_foods.lua:isFood]
- `findPlayerInPerimeter()` [movements_sacrifice_foods.lua:findPlayerInPerimeter]
- `foodSacrifice.onAddItem(moveitem, tileitem, position)` [movements_sacrifice_foods.lua:foodSacrifice.onAddItem]
- `MoveEvent()` assigned to `foodSacrifice` [movements_sacrifice_foods.lua:foodSacrifice]
- `MoveEvent()` registration [movements_sacrifice_foods.lua:MoveEvent]
- `startBattle(pid, position, b_name, middle)` [movements_teleportTo.lua:startBattle]
- `resetRoom(position, name)` [movements_teleportTo.lua:resetRoom]
- `movements_desert_teleportTo.onStepIn(creature, item, position, fromPosition)` [movements_teleportTo.lua:movements_desert_teleportTo.onStepIn]
- `MoveEvent()` assigned to `movements_desert_teleportTo` [movements_teleportTo.lua:movements_desert_teleportTo]
- `MoveEvent()` registration [movements_teleportTo.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_chests.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_doors.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_doors.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_totems.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_totems.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_color_puzzle.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_color_puzzle.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_sacrifice_foods.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_sacrifice_foods.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movements_sacrifice_foods.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_teleportTo.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_teleportTo.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_chests.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_chests.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_chests.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_doors.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_doors.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_doors.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_totems.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_totems.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_totems.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_totems.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_color_puzzle.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_color_puzzle.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
