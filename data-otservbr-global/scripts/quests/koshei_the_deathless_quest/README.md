# Koshei The Deathless Quest

## Overview
Component package under `scripts/quests/koshei_the_deathless_quest` containing 3 files (`action_bag.lua`..`action_switch.lua`).

## Interface
- `kosheiBag.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_bag.lua:kosheiBag.onUse]
- `Action()` assigned to `kosheiBag` [action_bag.lua:kosheiBag]
- `Action()` registration [action_bag.lua:Action]
- `kosheiBoss.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_boss.lua:kosheiBoss.onUse]
- `Action()` assigned to `kosheiBoss` [action_boss.lua:kosheiBoss]
- `Action()` registration [action_boss.lua:Action]
- `revertCoffin()` [action_switch.lua:revertCoffin]
- `kosheiSwitch.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_switch.lua:kosheiSwitch.onUse]
- `Action()` assigned to `kosheiSwitch` [action_switch.lua:kosheiSwitch]
- `Action()` registration [action_switch.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_bag.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_boss.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action_switch.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_bag.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_bag.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_bag.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_boss.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_boss.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_boss.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_switch.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_switch.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [action_switch.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
