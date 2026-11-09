# Soulpit

## Overview
Component package under `scripts/actions/soulpit` containing 2 files (`soulpit_arena_exit.lua`..`soulpit_entrance.lua`).

## Interface
- `soulpitArenaExit.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [soulpit_arena_exit.lua:soulpitArenaExit.onUse]
- `Action()` assigned to `soulpitArenaExit` [soulpit_arena_exit.lua:soulpitArenaExit]
- `Action()` registration [soulpit_arena_exit.lua:Action]
- `soulpitEntrance.onStepIn(creature, item, position, fromPosition)` [soulpit_entrance.lua:soulpitEntrance.onStepIn]
- `soulpitExit.onStepIn(creature, item, position, fromPosition)` [soulpit_entrance.lua:soulpitExit.onStepIn]
- `MoveEvent()` assigned to `soulpitEntrance` [soulpit_entrance.lua:soulpitEntrance]
- `MoveEvent()` assigned to `soulpitExit` [soulpit_entrance.lua:soulpitExit]
- `MoveEvent()` registration [soulpit_entrance.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [soulpit_entrance.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [soulpit_arena_exit.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [soulpit_arena_exit.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [soulpit_entrance.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [soulpit_entrance.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
