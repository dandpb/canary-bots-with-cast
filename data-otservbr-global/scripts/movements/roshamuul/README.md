# Roshamuul

## Overview
Component package under `scripts/movements/roshamuul` containing 1 files (`strange_vortex_tp.lua`..`strange_vortex_tp.lua`).

## Interface
- `nightmareVortex.onStepIn(creature, item, position, fromPosition)` [strange_vortex_tp.lua:nightmareVortex.onStepIn]
- `MoveEvent()` assigned to `nightmareVortex` [strange_vortex_tp.lua:nightmareVortex]
- `MoveEvent()` registration [strange_vortex_tp.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [strange_vortex_tp.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [strange_vortex_tp.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [strange_vortex_tp.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
