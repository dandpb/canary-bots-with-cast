# High And Dry Isles

## Overview
Component package under `scripts/quests/the_secret_library_quest/high_and_dry_isles` containing 3 files (`actions_telescope.lua`..`movements_stepIn.lua`).

## Interface
- `actions_isles_telescope.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_telescope.lua:actions_isles_telescope.onUse]
- `Action()` assigned to `actions_isles_telescope` [actions_telescope.lua:actions_isles_telescope]
- `Action()` registration [actions_telescope.lua:Action]
- `movements_isle_color_puzzle.onStepIn(creature, item, position, fromPosition)` [movements_boat_puzzle.lua:movements_isle_color_puzzle.onStepIn]
- `MoveEvent()` assigned to `movements_isle_color_puzzle` [movements_boat_puzzle.lua:movements_isle_color_puzzle]
- `MoveEvent()` registration [movements_boat_puzzle.lua:MoveEvent]
- `resetRoom(position)` [movements_stepIn.lua:resetRoom]
- `startBattle(pid, position, b_name, middle)` [movements_stepIn.lua:startBattle]
- `movements_isle_stepIn.onStepIn(creature, item, position, fromPosition)` [movements_stepIn.lua:movements_isle_stepIn.onStepIn]
- `MoveEvent()` assigned to `movements_isle_stepIn` [movements_stepIn.lua:movements_isle_stepIn]
- `MoveEvent()` registration [movements_stepIn.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_telescope.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_boat_puzzle.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_boat_puzzle.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_stepIn.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_stepIn.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_telescope.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_telescope.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_boat_puzzle.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_boat_puzzle.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_boat_puzzle.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [movements_boat_puzzle.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_stepIn.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_stepIn.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [movements_stepIn.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_stepIn.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [movements_stepIn.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [movements_stepIn.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
