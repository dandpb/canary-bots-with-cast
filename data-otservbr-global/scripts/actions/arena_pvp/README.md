# Arena Pvp

## Overview
Component package under `scripts/actions/arena_pvp` containing 2 files (`arena_10x10.lua`..`arena_2x2.lua`).

## Interface
- `arena10x10.onUse(player, item, fromPosition, target, toPosition, monster, isHotkey)` [arena_10x10.lua:arena10x10.onUse]
- `Action()` assigned to `arena10x10` [arena_10x10.lua:arena10x10]
- `Action()` registration [arena_10x10.lua:Action]
- `arena2x2.onUse(player, item, fromPosition, target, toPosition, monster, isHotkey)` [arena_2x2.lua:arena2x2.onUse]
- `Action()` assigned to `arena2x2` [arena_2x2.lua:arena2x2]
- `Action()` registration [arena_2x2.lua:Action]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [arena_10x10.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [arena_10x10.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [arena_2x2.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [arena_2x2.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [arena_10x10.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [arena_10x10.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [arena_2x2.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [arena_2x2.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
