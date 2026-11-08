# To Take Roots

## Overview
Component package under `scripts/quests/oramond/to_take_roots` containing 1 files (`actions_to_take_roots.lua`..`actions_to_take_roots.lua`).

## Interface
- `revertRoot(position, itemId, transformId)` [actions_to_take_roots.lua:revertRoot]
- `toTakeRoots.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_to_take_roots.lua:toTakeRoots.onUse]
- `Action()` assigned to `toTakeRoots` [actions_to_take_roots.lua:toTakeRoots]
- `Action()` registration [actions_to_take_roots.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_to_take_roots.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_to_take_roots.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_to_take_roots.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_to_take_roots.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_to_take_roots.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_to_take_roots.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
