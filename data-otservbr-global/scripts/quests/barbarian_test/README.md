# Barbarian Test

## Overview
Component package under `scripts/quests/barbarian_test` containing 2 files (`action_horn.lua`..`action_mead.lua`).

## Interface
- `sendSleepEffect(position)` [action_horn.lua:sendSleepEffect]
- `barbarianHorn.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_horn.lua:barbarianHorn.onUse]
- `Action()` assigned to `barbarianHorn` [action_horn.lua:barbarianHorn]
- `Action()` registration [action_horn.lua:Action]
- `barbarianMead.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_mead.lua:barbarianMead.onUse]
- `Action()` assigned to `barbarianMead` [action_mead.lua:barbarianMead]
- `Action()` registration [action_mead.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_horn.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action_horn.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_mead.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_horn.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_horn.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_horn.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [action_horn.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_mead.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_mead.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
