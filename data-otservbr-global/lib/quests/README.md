# Quests

## Overview
Component package under `lib/quests` containing 11 files (`bigfoot_burden.lua`..`their_masters_voice.lua`).

## Interface
- Lua script module `bigfoot_burden.lua` [bigfoot_burden.lua:module]
- Global symbol `DEMON_OAK_POSITION` [demon_oak.lua:DEMON_OAK_POSITION]
- Global symbol `DEMON_OAK_KICK_POSITION` [demon_oak.lua:DEMON_OAK_KICK_POSITION]
- Global symbol `DEMON_OAK_ENTER_POSITION` [demon_oak.lua:DEMON_OAK_ENTER_POSITION]
- Global symbol `DEMON_OAK_REWARDROOM_POSITION` [demon_oak.lua:DEMON_OAK_REWARDROOM_POSITION]
- `teleportPlayer(playerId, pos)` [grimvale.lua:teleportPlayer]
- `loadMap()` [grimvale.lua:loadMap]
- `removeFeroxa(feroxa)` [grimvale.lua:removeFeroxa]
- `final()` [grimvale.lua:final]
- `removeItems()` [grimvale.lua:removeItems]
- `grimvaleSpectators()` [grimvale.lua:grimvaleSpectators]
- `Player.getPawAndFurRank(self)` [killing_in_the_name_of.lua:Player.getPawAndFurRank]
- `Player.getPawAndFurPoints(self)` [killing_in_the_name_of.lua:Player.getPawAndFurPoints]
- `getTaskByName(name, table)` [killing_in_the_name_of.lua:getTaskByName]
- `Player.getTasks(self)` [killing_in_the_name_of.lua:Player.getTasks]
- `Player.canStartTask(self, name, table)` [killing_in_the_name_of.lua:Player.canStartTask]
- `Player.getStartedTasks(self)` [killing_in_the_name_of.lua:Player.getStartedTasks]
- `getPlayerRank(cid)` [killing_in_the_name_of.lua:getPlayerRank]
- `getPlayerTasksPoints(cid)` [killing_in_the_name_of.lua:getPlayerTasksPoints]
- `getTasksByPlayer(cid)` [killing_in_the_name_of.lua:getTasksByPlayer]
- `canStartTask(cid, name, table)` [killing_in_the_name_of.lua:canStartTask]
- `getPlayerStartedTasks(cid)` [killing_in_the_name_of.lua:getPlayerStartedTasks]
- Global symbol `RANK_NONE` [killing_in_the_name_of.lua:RANK_NONE]
- Global symbol `RANK_JOIN` [killing_in_the_name_of.lua:RANK_JOIN]
- Global symbol `RANK_HUNTSMAN` [killing_in_the_name_of.lua:RANK_HUNTSMAN]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [bigfoot_burden.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [grimvale.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [grimvale.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [grimvale.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [killing_in_the_name_of.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [soul_war.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [soul_war.lua:Tile]
- Quest mission states map strictly to `Storage.Quest` keys for `"Greenhorn"` [svargrond_arena.lua:missions]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [svargrond_arena.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [svargrond_arena.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [svargrond_arena.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [their_masters_voice.lua:Tile]

## Side Effects
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [bigfoot_burden.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [bigfoot_burden.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [bigfoot_burden.lua:transform]
- Mutates player or global storage state via `setStorageValue` [grimvale.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [grimvale.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [grimvale.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [grimvale.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [grimvale.lua:addEvent]
- Loads and executes `DATA_DIRECTORY .. "/lib/quests/bigfoot_burden.lua"` via `dofile` [quest.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/lib/quests/demon_oak.lua"` via `dofile` [quest.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/lib/quests/grimvale.lua"` via `dofile` [quest.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/lib/quests/killing_in_the_name_of.lua"` via `dofile` [quest.lua:dofile]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
