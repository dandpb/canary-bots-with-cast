# The Ancient Sewers

## Overview
Component package under `scripts/quests/oramond/the_ancient_sewers` containing 1 files (`actions_the_ancient_sewers.lua`..`actions_the_ancient_sewers.lua`).

## Interface
- `revertItem(toPosition, getItemId, itemTransform)` [actions_the_ancient_sewers.lua:revertItem]
- `theAncientSewers.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_the_ancient_sewers.lua:theAncientSewers.onUse]
- `Action()` assigned to `theAncientSewers` [actions_the_ancient_sewers.lua:theAncientSewers]
- `Action()` registration [actions_the_ancient_sewers.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_the_ancient_sewers.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_the_ancient_sewers.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_the_ancient_sewers.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_the_ancient_sewers.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_the_ancient_sewers.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_the_ancient_sewers.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
