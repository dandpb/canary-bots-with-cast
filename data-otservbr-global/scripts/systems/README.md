# Systems

## Overview
Component package under `scripts/systems` containing 1 files (`hazard_primal.lua`..`hazard_primal.lua`).

## Interface
- `primalPod.onStepIn(creature, item, position, fromPosition)` [hazard_primal.lua:primalPod.onStepIn]
- `createPrimalPod(position)` [hazard_primal.lua:createPrimalPod]
- `spawnEvent.onSpawn(monster, position)` [hazard_primal.lua:spawnEvent.onSpawn]
- `deathEvent.onDeath(creature)` [hazard_primal.lua:deathEvent.onDeath]
- `MoveEvent()` assigned to `primalPod` [hazard_primal.lua:primalPod]
- `MoveEvent()` registration [hazard_primal.lua:MoveEvent]
- `CreatureEvent("PrimalHazardDeath")` assigned to `deathEvent` [hazard_primal.lua:deathEvent]
- `CreatureEvent("PrimalHazardDeath")` registration [hazard_primal.lua:CreatureEvent]
- `ZoneEvent(hazardZone)` assigned to `spawnEvent` [hazard_primal.lua:spawnEvent]
- `ZoneEvent(hazardZone)` registration [hazard_primal.lua:ZoneEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [hazard_primal.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [hazard_primal.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [hazard_primal.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [hazard_primal.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [hazard_primal.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [hazard_primal.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
