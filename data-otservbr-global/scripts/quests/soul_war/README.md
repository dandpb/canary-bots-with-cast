# Soul War

## Overview
Component package under `scripts/quests/soul_war` containing 12 files (`action-reward_soul_war.lua`..`spell-soulsnatcher.lua`).

## Interface
- `rewardSoulWar.onUse(creature, item, fromPosition, target, toPosition, isHotkey)` [action-reward_soul_war.lua:rewardSoulWar.onUse]
- `Action()` assigned to `rewardSoulWar` [action-reward_soul_war.lua:rewardSoulWar]
- `Action()` registration [action-reward_soul_war.lua:Action]
- `createTeleportEffect(position)` [eventcallback_on_combat_taint.lua:createTeleportEffect]
- `scheduleMonsterCreation(player, monster, monsterName, spawnPosition)` [eventcallback_on_combat_taint.lua:scheduleMonsterCreation]
- `onPlayerAttackMonster(player, target)` [eventcallback_on_combat_taint.lua:onPlayerAttackMonster]
- `onMonsterAttackPlayer(target, primaryValue, secondaryValue)` [eventcallback_on_combat_taint.lua:onMonsterAttackPlayer]
- `callback.creatureOnCombat(caster, target, damage)` [eventcallback_on_combat_taint.lua:callback.creatureOnCombat]
- `callback.playerOnThink(player, interval)` [eventcallback_on_combat_taint.lua:callback.playerOnThink]
- `EventCallback("CreatureOnCombatTaint")` assigned to `callback` [eventcallback_on_combat_taint.lua:callback]
- `EventCallback("PlayerOnThinkTaint")` assigned to `callback` [eventcallback_on_combat_taint.lua:callback]
- `EventCallback("CreatureOnCombatTaint")` registration [eventcallback_on_combat_taint.lua:EventCallback]
- `EventCallback("PlayerOnThinkTaint")` registration [eventcallback_on_combat_taint.lua:EventCallback]
- `updateWaterPoolsSize()` [globalevent-ebb_and_flow_change_maps.lua:updateWaterPoolsSize]
- `clearPendingEvents()` [globalevent-ebb_and_flow_change_maps.lua:clearPendingEvents]
- `unregisterEventCallbacks()` [globalevent-ebb_and_flow_change_maps.lua:unregisterEventCallbacks]
- `loadMapEmpty()` [globalevent-ebb_and_flow_change_maps.lua:loadMapEmpty]
- `updatePlayers.mapOnLoad(mapPath)` [globalevent-ebb_and_flow_change_maps.lua:updatePlayers.mapOnLoad]
- `getDistance(pos1, pos2)` [globalevent-ebb_and_flow_change_maps.lua:getDistance]
- `findNearestRoomPosition(playerPosition)` [globalevent-ebb_and_flow_change_maps.lua:findNearestRoomPosition]
- `loadMapInundate()` [globalevent-ebb_and_flow_change_maps.lua:loadMapInundate]
- `loadEmptyMap.onStartup()` [globalevent-ebb_and_flow_change_maps.lua:loadEmptyMap.onStartup]
- `eddAndFlowInundate.onThink(interval, lastExecution)` [globalevent-ebb_and_flow_change_maps.lua:eddAndFlowInundate.onThink]
- `cleanupOnSave.onSave()` [globalevent-ebb_and_flow_change_maps.lua:cleanupOnSave.onSave]
- `GlobalEvent("SoulWarQuest.ebbAndFlow")` assigned to `loadEmptyMap` [globalevent-ebb_and_flow_change_maps.lua:loadEmptyMap]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [action-reward_soul_war.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [eventcallback_on_combat_taint.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [globalevent-ebb_and_flow_change_maps.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [globalevent-ebb_and_flow_change_maps.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [moveevent-claustrophobic-inferno-raid.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [moveevent-soul_war_entrances.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [moveevent-teleport_entrance_reward.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [soul_war_mechanics.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [soul_war_mechanics.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [spell-eye_beam.lua:Tile]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [spell-eye_beam.lua:combat]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [spell-fire_beam_cruelty.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-reward_soul_war.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action-reward_soul_war.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [eventcallback_on_combat_taint.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [eventcallback_on_combat_taint.lua:Game]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [eventcallback_on_combat_taint.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [globalevent-ebb_and_flow_change_maps.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [globalevent-ebb_and_flow_change_maps.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [globalevent-ebb_and_flow_change_maps.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [globalevent-ebb_and_flow_change_maps.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [moveevent-claustrophobic-inferno-raid.lua:register]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [moveevent-claustrophobic-inferno-raid.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [moveevent-soul_war_entrances.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
