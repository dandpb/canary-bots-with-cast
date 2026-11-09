# Shrines

## Overview
Component package under `scripts/actions/shrines` containing 1 files (`feyrist_exit.lua`..`feyrist_exit.lua`).

## Interface
- `feyristExit.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [feyrist_exit.lua:feyristExit.onUse]
- `Action()` assigned to `feyristExit` [feyrist_exit.lua:feyristExit]
- `Action()` registration [feyrist_exit.lua:Action]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [feyrist_exit.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [feyrist_exit.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
