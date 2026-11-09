# Dreamers Challenge Quest

## Overview
Component package under `scripts/quests/dreamers_challenge_quest` containing 21 files (`actions_documents.lua`..`movement_wall_teleport.lua`).

## Interface
- `dreamerDocuments.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_documents.lua:dreamerDocuments.onUse]
- `Action()` assigned to `dreamerDocuments` [actions_documents.lua:dreamerDocuments]
- `Action()` registration [actions_documents.lua:Action]
- `revertLever(position)` [actions_lever_brotherhood.lua:revertLever]
- `dreamerBrotherhoodLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lever_brotherhood.lua:dreamerBrotherhoodLever.onUse]
- `Action()` assigned to `dreamerBrotherhoodLever` [actions_lever_brotherhood.lua:dreamerBrotherhoodLever]
- `Action()` registration [actions_lever_brotherhood.lua:Action]
- `revertLever(position)` [actions_lever_nightmare.lua:revertLever]
- `dreamerNightmareLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lever_nightmare.lua:dreamerNightmareLever.onUse]
- `Action()` assigned to `dreamerNightmareLever` [actions_lever_nightmare.lua:dreamerNightmareLever]
- `Action()` registration [actions_lever_nightmare.lua:Action]
- `dreamerStone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_stone_teleport.lua:dreamerStone.onUse]
- `Action()` assigned to `dreamerStone` [actions_stone_teleport.lua:dreamerStone]
- `Action()` registration [actions_stone_teleport.lua:Action]
- `dreamerTicTac.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_tic_tac.lua:dreamerTicTac.onUse]
- `Action()` assigned to `dreamerTicTac` [actions_tic_tac.lua:dreamerTicTac]
- `Action()` registration [actions_tic_tac.lua:Action]
- `dreamerTicTacTeleport.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_tic_tac_teleport.lua:dreamerTicTacTeleport.onUse]
- `Action()` assigned to `dreamerTicTacTeleport` [actions_tic_tac_teleport.lua:dreamerTicTacTeleport]
- `Action()` registration [actions_tic_tac_teleport.lua:Action]
- `revertLever(position)` [actions_walls.lua:revertLever]
- `dreamerWalls.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_walls.lua:dreamerWalls.onUse]
- `Action()` assigned to `dreamerWalls` [actions_walls.lua:dreamerWalls]
- `Action()` registration [actions_walls.lua:Action]
- `carrot.onStepIn(creature, item, position, fromPosition)` [movement_carrot.lua:carrot.onStepIn]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_documents.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lever_brotherhood.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_lever_brotherhood.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lever_nightmare.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_lever_nightmare.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_stone_teleport.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_tic_tac_teleport.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_walls.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_carrot.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_clock_tile.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_court_teleport.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movement_death_ring.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_documents.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_documents.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lever_brotherhood.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_lever_brotherhood.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_lever_brotherhood.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_lever_brotherhood.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_lever_brotherhood.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lever_nightmare.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_lever_nightmare.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_lever_nightmare.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_lever_nightmare.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_lever_nightmare.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
