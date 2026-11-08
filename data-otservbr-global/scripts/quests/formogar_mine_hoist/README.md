# Formogar Mine Hoist

## Overview
Component package under `scripts/quests/formogar_mine_hoist` containing 1 files (`movements_hoist.lua`..`movements_hoist.lua`).

## Interface
- `hoist.onStepIn(creature, item, position, fromPosition)` [movements_hoist.lua:hoist.onStepIn]
- `MoveEvent()` assigned to `hoist` [movements_hoist.lua:hoist]
- `MoveEvent()` registration [movements_hoist.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_hoist.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_hoist.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movements_hoist.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_hoist.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_hoist.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
