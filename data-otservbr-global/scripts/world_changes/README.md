# World Changes

## Overview
Component package under `scripts/world_changes` containing 6 files (`fury_gates.lua`..`their_masters_voice.lua`).

## Interface
- `furyWebhook(message)` [fury_gates.lua:furyWebhook]
- `furyGates.onStartup(interval)` [fury_gates.lua:furyGates.onStartup]
- `furyGatesTeleports.onStepIn(creature, item, position, fromPosition)` [fury_gates.lua:furyGatesTeleports.onStepIn]
- `MoveEvent()` assigned to `furyGatesTeleports` [fury_gates.lua:furyGatesTeleports]
- `MoveEvent()` registration [fury_gates.lua:MoveEvent]
- `GlobalEvent("Load Fury Gates")` assigned to `furyGates` [fury_gates.lua:furyGates]
- `GlobalEvent("Load Fury Gates")` registration [fury_gates.lua:GlobalEvent]
- `createRandomMonster(position, availableMonsters)` [grimvale_respawn_event.lua:createRandomMonster]
- `spawnMonsters(monstersToSpawn)` [grimvale_respawn_event.lua:spawnMonsters]
- `grimvaleRespawnEvent.onStartup()` [grimvale_respawn_event.lua:grimvaleRespawnEvent.onStartup]
- `GlobalEvent("GrimvaleRespawnEvent")` assigned to `grimvaleRespawnEvent` [grimvale_respawn_event.lua:grimvaleRespawnEvent]
- `GlobalEvent("GrimvaleRespawnEvent")` registration [grimvale_respawn_event.lua:GlobalEvent]
- `Nightmarewebhook(message)` [nightmare_isles.lua:Nightmarewebhook]
- `nightmareIsleEvent.onStartup()` [nightmare_isles.lua:nightmareIsleEvent.onStartup]
- `teleportExit.onStepIn(creature, item, position, fromPosition)` [nightmare_isles.lua:teleportExit.onStepIn]
- `teleportEntrace.onStepIn(creature, item, position, fromPosition)` [nightmare_isles.lua:teleportEntrace.onStepIn]
- `teleportLadder.onStepIn(creature, item, position, fromPosition)` [nightmare_isles.lua:teleportLadder.onStepIn]
- `MoveEvent()` assigned to `teleportExit` [nightmare_isles.lua:teleportExit]
- `MoveEvent()` assigned to `teleportEntrace` [nightmare_isles.lua:teleportEntrace]
- `MoveEvent()` assigned to `teleportLadder` [nightmare_isles.lua:teleportLadder]
- `MoveEvent()` registration [nightmare_isles.lua:MoveEvent]
- `GlobalEvent("Nightmare Isle")` assigned to `nightmareIsleEvent` [nightmare_isles.lua:nightmareIsleEvent]
- `GlobalEvent("Nightmare Isle")` registration [nightmare_isles.lua:GlobalEvent]
- `yasirwebhook(message)` [oriental_trader.lua:yasirwebhook]
- `spawnYasir(position)` [oriental_trader.lua:spawnYasir]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [fury_gates.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [fury_gates.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [grimvale_respawn_event.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [nightmare_isles.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [nightmare_isles.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [oriental_trader.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [their_masters_voice.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [fury_gates.lua:register]
- Mutates player or global storage state via `setStorageValue` [fury_gates.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [fury_gates.lua:teleportTo]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [fury_gates.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [grimvale_respawn_event.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [grimvale_respawn_event.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [grimvale_respawn_event.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [nightmare_isles.lua:register]
- Mutates player or global storage state via `setStorageValue` [nightmare_isles.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [nightmare_isles.lua:teleportTo]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [nightmare_isles.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [oriental_trader.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
