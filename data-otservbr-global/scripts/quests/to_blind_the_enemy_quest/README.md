# To Blind The Enemy Quest

## Overview
Component package under `scripts/quests/to_blind_the_enemy_quest` containing 1 files (`mirror.lua`..`mirror.lua`).

## Interface
- `revertItem(position, itemId)` [mirror.lua:revertItem]
- `mirror.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [mirror.lua:mirror.onUse]
- `Action()` assigned to `mirror` [mirror.lua:mirror]
- `Action()` registration [mirror.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [mirror.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [mirror.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [mirror.lua:register]
- Mutates player or global storage state via `setStorageValue` [mirror.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [mirror.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [mirror.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
