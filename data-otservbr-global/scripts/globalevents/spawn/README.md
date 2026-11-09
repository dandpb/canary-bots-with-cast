# Spawn

## Overview
Component package under `scripts/globalevents/spawn` containing 1 files (`rashid.lua`..`rashid.lua`).

## Interface
- `rashidwebhook(message)` [rashid.lua:rashidwebhook]
- `rashid.onStartup()` [rashid.lua:rashid.onStartup]
- `rashidSpawnOnTime.onTime(interval)` [rashid.lua:rashidSpawnOnTime.onTime]
- `GlobalEvent("rashid")` assigned to `rashid` [rashid.lua:rashid]
- `GlobalEvent("rashidSpawnOnTime")` assigned to `rashidSpawnOnTime` [rashid.lua:rashidSpawnOnTime]
- `GlobalEvent("rashid")` registration [rashid.lua:GlobalEvent]
- `GlobalEvent("rashidSpawnOnTime")` registration [rashid.lua:GlobalEvent]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [rashid.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [rashid.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [rashid.lua:teleportTo]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [rashid.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
