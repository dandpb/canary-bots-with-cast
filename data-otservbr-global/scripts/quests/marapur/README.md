# Marapur

## Overview
Component package under `scripts/quests/marapur` containing 4 files (`actions_boss_timira_fight.lua`..`timira_the_many-headed.lua`).

## Interface
- `restartShatteredWater()` [actions_boss_timira_fight.lua:restartShatteredWater]
- `restartBuckets()` [actions_boss_timira_fight.lua:restartBuckets]
- `restartTeleports()` [actions_boss_timira_fight.lua:restartTeleports]
- `removeRewardChests()` [actions_boss_timira_fight.lua:removeRewardChests]
- `restart()` [actions_boss_timira_fight.lua:restart]
- `activeZone()` [actions_boss_timira_fight.lua:activeZone]
- `startSecondStage()` [actions_boss_timira_fight.lua:startSecondStage]
- `startThirdStage()` [actions_boss_timira_fight.lua:startThirdStage]
- `encounter:onReset(position)` [actions_boss_timira_fight.lua:encounter:onReset]
- `nagaSpawner.onThink(interval, lastExecution)` [actions_boss_timira_fight.lua:nagaSpawner.onThink]
- `sparklingWater.onThink(interval, lastExecution)` [actions_boss_timira_fight.lua:sparklingWater.onThink]
- `timiraBucket.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_boss_timira_fight.lua:timiraBucket.onUse]
- `corruptedWater.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_boss_timira_fight.lua:corruptedWater.onUse]
- `timiraChest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_boss_timira_fight.lua:timiraChest.onUse]
- `Action()` assigned to `timiraBucket` [actions_boss_timira_fight.lua:timiraBucket]
- `Action()` assigned to `corruptedWater` [actions_boss_timira_fight.lua:corruptedWater]
- `Action()` assigned to `timiraChest` [actions_boss_timira_fight.lua:timiraChest]
- `Action()` registration [actions_boss_timira_fight.lua:Action]
- `GlobalEvent("self.timira.spawner.onThink")` assigned to `nagaSpawner` [actions_boss_timira_fight.lua:nagaSpawner]
- `GlobalEvent("self.timira.water.onThink")` assigned to `sparklingWater` [actions_boss_timira_fight.lua:sparklingWater]
- `GlobalEvent("self.timira.spawner.onThink")` registration [actions_boss_timira_fight.lua:GlobalEvent]
- `GlobalEvent("self.timira.water.onThink")` registration [actions_boss_timira_fight.lua:GlobalEvent]
- `Encounter("Timira the Many-Headed", {
	zone = fightZone,
	timeToSpawnMonsters = "10ms",
})` assigned to `encounter` [actions_boss_timira_fight.lua:encounter]
- `Encounter("Timira the Many-Headed", {
	zone = fightZone,
	timeToSpawnMonsters = "10ms",
})` registration [actions_boss_timira_fight.lua:Encounter]
- `Zone("fight.timira.encounterZone")` assigned to `fightZone` [actions_boss_timira_fight.lua:fightZone]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_boss_timira_fight.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_teleports_timira.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_ramp_to_north-temple.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_boss_timira_fight.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_boss_timira_fight.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_boss_timira_fight.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_boss_timira_fight.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_teleports_timira.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_teleports_timira.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_ramp_to_north-temple.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_ramp_to_north-temple.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [timira_the_many-headed.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
