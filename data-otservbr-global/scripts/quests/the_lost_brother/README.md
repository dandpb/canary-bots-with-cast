# The Lost Brother

## Overview
Component package under `scripts/quests/the_lost_brother` containing 2 files (`actions_asura_mirror.lua`..`movement-find-remains.lua`).

## Interface
- `theLostAsura.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_asura_mirror.lua:theLostAsura.onUse]
- `Action()` assigned to `theLostAsura` [actions_asura_mirror.lua:theLostAsura]
- `Action()` registration [actions_asura_mirror.lua:Action]
- `findRemains.onStepIn(creature, item, position, fromPosition)` [movement-find-remains.lua:findRemains.onStepIn]
- `MoveEvent()` assigned to `findRemains` [movement-find-remains.lua:findRemains]
- `MoveEvent()` registration [movement-find-remains.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement-find-remains.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement-find-remains.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_asura_mirror.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_asura_mirror.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement-find-remains.lua:register]
- Mutates player or global storage state via `setStorageValue` [movement-find-remains.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
