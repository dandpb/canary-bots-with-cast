# Elemental Spheres

## Overview
Component package under `scripts/quests/elemental_spheres` containing 11 files (`actions_lever.lua`..`movements_summon_overlord.lua`).

## Interface
- `elementalSpheresLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lever.lua:elementalSpheresLever.onUse]
- `Action()` assigned to `elementalSpheresLever` [actions_lever.lua:elementalSpheresLever]
- `Action()` registration [actions_lever.lua:Action]
- `resetRoom(players)` [actions_lord_of_elements_lever.lua:resetRoom]
- `warnPlayers(players)` [actions_lord_of_elements_lever.lua:warnPlayers]
- `areMachinesCharged()` [actions_lord_of_elements_lever.lua:areMachinesCharged]
- `elementalSpheresLordLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lord_of_elements_lever.lua:elementalSpheresLordLever.onUse]
- `Action()` assigned to `elementalSpheresLordLever` [actions_lord_of_elements_lever.lua:elementalSpheresLordLever]
- `Action()` registration [actions_lord_of_elements_lever.lua:Action]
- `elementalSpheresMachine1.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_machine1.lua:elementalSpheresMachine1.onUse]
- `Action()` assigned to `elementalSpheresMachine1` [actions_machine1.lua:elementalSpheresMachine1]
- `Action()` registration [actions_machine1.lua:Action]
- `elementalSpheresMachine2.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_machine2.lua:elementalSpheresMachine2.onUse]
- `Action()` assigned to `elementalSpheresMachine2` [actions_machine2.lua:elementalSpheresMachine2]
- `Action()` registration [actions_machine2.lua:Action]
- `elementalSpheresSouls1.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_soils1.lua:elementalSpheresSouls1.onUse]
- `Action()` assigned to `elementalSpheresSouls1` [actions_soils1.lua:elementalSpheresSouls1]
- `Action()` registration [actions_soils1.lua:Action]
- `elementalSpheresSoils2.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_soils2.lua:elementalSpheresSoils2.onUse]
- `Action()` assigned to `elementalSpheresSoils2` [actions_soils2.lua:elementalSpheresSoils2]
- `Action()` registration [actions_soils2.lua:Action]
- `elementalSpheresOver.onDeath(creature)` [creaturescripts_overlord_kill.lua:elementalSpheresOver.onDeath]
- `CreatureEvent("ElementalOverlordDeath")` assigned to `elementalSpheresOver` [creaturescripts_overlord_kill.lua:elementalSpheresOver]
- `CreatureEvent("ElementalOverlordDeath")` registration [creaturescripts_overlord_kill.lua:CreatureEvent]
- `aoeTeleportOut.onStepIn(creature, item, position, fromPosition)` [movements_aoe_teleport_out.lua:aoeTeleportOut.onStepIn]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lever.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_lever.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lord_of_elements_lever.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_lord_of_elements_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_machine1.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_machine1.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_machine2.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_overlord_kill.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_aoe_teleport_out.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_soil_entrance.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_soil_exit.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lever.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_lever.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lord_of_elements_lever.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_lord_of_elements_lever.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_lord_of_elements_lever.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_lord_of_elements_lever.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_lord_of_elements_lever.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_lord_of_elements_lever.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_machine1.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_machine1.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_machine1.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
