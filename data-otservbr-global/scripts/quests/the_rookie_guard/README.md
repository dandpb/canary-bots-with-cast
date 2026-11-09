# The Rookie Guard

## Overview
Component package under `scripts/quests/the_rookie_guard` containing 11 files (`mission02_defence.lua`..`missions.lua`).

## Interface
- `missionGuide.onStepIn(creature, item, position, fromPosition)` [mission02_defence.lua:missionGuide.onStepIn]
- `stonePile.onUse(player, item, frompos, item2, topos)` [mission02_defence.lua:stonePile.onUse]
- `heavyStone.onUse(player, item, frompos, item2, topos)` [mission02_defence.lua:heavyStone.onUse]
- `Action()` assigned to `stonePile` [mission02_defence.lua:stonePile]
- `Action()` assigned to `heavyStone` [mission02_defence.lua:heavyStone]
- `Action()` registration [mission02_defence.lua:Action]
- `MoveEvent()` assigned to `missionGuide` [mission02_defence.lua:missionGuide]
- `MoveEvent()` registration [mission02_defence.lua:MoveEvent]
- `ratKill.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [mission03_rational_request.lua:ratKill.onDeath]
- `CreatureEvent("RationalRequestRatDeath")` assigned to `ratKill` [mission03_rational_request.lua:ratKill]
- `CreatureEvent("RationalRequestRatDeath")` registration [mission03_rational_request.lua:CreatureEvent]
- `missionGuide.onStepIn(creature, item, position, fromPosition)` [mission04_home_brewed.lua:missionGuide.onStepIn]
- `MoveEvent()` assigned to `missionGuide` [mission04_home_brewed.lua:missionGuide]
- `MoveEvent()` registration [mission04_home_brewed.lua:MoveEvent]
- `missionGuide.onStepIn(creature, item, position, fromPosition)` [mission05_web_terror.lua:missionGuide.onStepIn]
- `spiderLairHole.onStepIn(creature, item, position, fromPosition)` [mission05_web_terror.lua:spiderLairHole.onStepIn]
- `greasyStone.onUse(player, item, frompos, item2, topos)` [mission05_web_terror.lua:greasyStone.onUse]
- `spiderQueenChamberHole.onStepIn(creature, item, position, fromPosition)` [mission05_web_terror.lua:spiderQueenChamberHole.onStepIn]
- `spiderWeb.onUse(player, item, frompos, item2, topos)` [mission05_web_terror.lua:spiderWeb.onUse]
- `Action()` assigned to `greasyStone` [mission05_web_terror.lua:greasyStone]
- `Action()` assigned to `spiderWeb` [mission05_web_terror.lua:spiderWeb]
- `Action()` registration [mission05_web_terror.lua:Action]
- `MoveEvent()` assigned to `missionGuide` [mission05_web_terror.lua:missionGuide]
- `MoveEvent()` assigned to `spiderLairHole` [mission05_web_terror.lua:spiderLairHole]
- `MoveEvent()` assigned to `spiderQueenChamberHole` [mission05_web_terror.lua:spiderQueenChamberHole]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [mission02_defence.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [mission02_defence.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [mission03_rational_request.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [mission04_home_brewed.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [mission04_home_brewed.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [mission05_web_terror.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [mission05_web_terror.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [mission06_run_like_wolf.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [mission06_run_like_wolf.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [mission07_attack.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [mission07_attack.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [mission07_attack.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [mission02_defence.lua:register]
- Mutates player or global storage state via `setStorageValue` [mission02_defence.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [mission02_defence.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [mission02_defence.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [mission03_rational_request.lua:register]
- Mutates player or global storage state via `setStorageValue` [mission03_rational_request.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [mission04_home_brewed.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [mission05_web_terror.lua:register]
- Mutates player or global storage state via `setStorageValue` [mission05_web_terror.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [mission05_web_terror.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [mission06_run_like_wolf.lua:register]
- Mutates player or global storage state via `setStorageValue` [mission06_run_like_wolf.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
