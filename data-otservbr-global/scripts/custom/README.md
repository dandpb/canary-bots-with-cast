# Custom

## Overview
Component package under `scripts/custom` containing 4 files (`ambient_sounds.lua`..`movement_trainer_exit.lua`).

## Interface
- `getCurrentSound(zoneData, period)` [ambient_sounds.lua:getCurrentSound]
- `getEffectivePeriod()` [ambient_sounds.lua:getEffectivePeriod]
- `zoneEvent.afterEnter(_, creature)` [ambient_sounds.lua:zoneEvent.afterEnter]
- `zoneEvent.afterLeave(_, creature)` [ambient_sounds.lua:zoneEvent.afterLeave]
- `ambientSoundPeriodChange.onPeriodChange(period)` [ambient_sounds.lua:ambientSoundPeriodChange.onPeriodChange]
- `GlobalEvent("AmbientSoundPeriodChange")` assigned to `ambientSoundPeriodChange` [ambient_sounds.lua:ambientSoundPeriodChange]
- `GlobalEvent("AmbientSoundPeriodChange")` registration [ambient_sounds.lua:GlobalEvent]
- `ZoneEvent(zone)` assigned to `zoneEvent` [ambient_sounds.lua:zoneEvent]
- `ZoneEvent(zone)` registration [ambient_sounds.lua:ZoneEvent]
- `Zone(zoneData.zone)` assigned to `zone` [ambient_sounds.lua:zone]
- `Zone(zoneData.zone)` registration [ambient_sounds.lua:Zone]
- `forcePeriodCommand.onSay(player, words, param)` [force_period.lua:forcePeriodCommand.onSay]
- `TalkAction("/forceperiod")` assigned to `forcePeriodCommand` [force_period.lua:forcePeriodCommand]
- `TalkAction("/forceperiod")` registration [force_period.lua:TalkAction]
- `isBusyable(position)` [movement_trainer_entrance.lua:isBusyable]
- `calculatingRoom(uid, position, column, line)` [movement_trainer_entrance.lua:calculatingRoom]
- `trainerEntrance.onStepIn(creature, item, position, fromPosition)` [movement_trainer_entrance.lua:trainerEntrance.onStepIn]
- `MoveEvent()` assigned to `trainerEntrance` [movement_trainer_entrance.lua:trainerEntrance]
- `MoveEvent()` registration [movement_trainer_entrance.lua:MoveEvent]
- `teleportToTemple(creature)` [movement_trainer_exit.lua:teleportToTemple]
- `trainerExit.onStepIn(creature, item, position, fromPosition)` [movement_trainer_exit.lua:trainerExit.onStepIn]
- `MoveEvent()` assigned to `trainerExit` [movement_trainer_exit.lua:trainerExit]
- `MoveEvent()` registration [movement_trainer_exit.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [ambient_sounds.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_trainer_entrance.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movement_trainer_entrance.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_trainer_exit.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [ambient_sounds.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [force_period.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement_trainer_entrance.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [movement_trainer_entrance.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [movement_trainer_entrance.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement_trainer_exit.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movement_trainer_exit.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
