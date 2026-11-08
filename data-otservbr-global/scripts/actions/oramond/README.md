# Oramond

## Overview
Component package under `scripts/actions/oramond` containing 5 files (`elevator.lua`..`teleport_west.lua`).

## Interface
- `elevator.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [elevator.lua:elevator.onUse]
- `Action()` assigned to `elevator` [elevator.lua:elevator]
- `Action()` registration [elevator.lua:Action]
- `sewerGrate.onUse(cid, item, fromPosition, itemEx, toPosition)` [sewer_grate.lua:sewerGrate.onUse]
- `Action()` assigned to `sewerGrate` [sewer_grate.lua:sewerGrate]
- `Action()` registration [sewer_grate.lua:Action]
- `sewerGrateTeleport.onUse(cid, item, fromPosition, itemEx, toPosition)` [sewer_grate_teleport.lua:sewerGrateTeleport.onUse]
- `Action()` assigned to `sewerGrateTeleport` [sewer_grate_teleport.lua:sewerGrateTeleport]
- `Action()` registration [sewer_grate_teleport.lua:Action]
- `teleportNorth.onUse(cid, item, fromPosition, itemEx, toPosition)` [teleport_north.lua:teleportNorth.onUse]
- `Action()` assigned to `teleportNorth` [teleport_north.lua:teleportNorth]
- `Action()` registration [teleport_north.lua:Action]
- `teleportWest.onUse(cid, item, fromPosition, itemEx, toPosition)` [teleport_west.lua:teleportWest.onUse]
- `Action()` assigned to `teleportWest` [teleport_west.lua:teleportWest]
- `Action()` registration [teleport_west.lua:Action]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [elevator.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [elevator.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [elevator.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [sewer_grate.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [sewer_grate_teleport.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [teleport_north.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [teleport_west.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
