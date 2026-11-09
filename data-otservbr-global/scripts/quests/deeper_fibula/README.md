# Deeper Fibula

## Overview
Component package under `scripts/quests/deeper_fibula` containing 1 files (`action-draw_well.lua`..`action-draw_well.lua`).

## Interface
- `drawWell.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-draw_well.lua:drawWell.onUse]
- `Action()` assigned to `drawWell` [action-draw_well.lua:drawWell]
- `Action()` registration [action-draw_well.lua:Action]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-draw_well.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [action-draw_well.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
