# Kilmaresh Quest

## Overview
Provides 25 direct files (`actions_augerfun.lua`..`movements_tpvoc.lua`) and 1 subdirectories under `scripts/quests/kilmaresh_quest`.

## Interface
- `augerfun.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_augerfun.lua:augerfun.onUse]
- `Action()` assigned to `augerfun` [actions_augerfun.lua:augerfun]
- `Action()` registration [actions_augerfun.lua:Action]
- `basin.onUse(player, item, frompos, item2, topos)` [actions_basin.lua:basin.onUse]
- `Action()` assigned to `basin` [actions_basin.lua:basin]
- `Action()` registration [actions_basin.lua:Action]
- `cagekey.onUse(player, item, frompos, item2, topos)` [actions_cagekey.lua:cagekey.onUse]
- `Action()` assigned to `cagekey` [actions_cagekey.lua:cagekey]
- `Action()` registration [actions_cagekey.lua:Action]
- `coruja.onUse(player, item, frompos, item2, topos)` [actions_coruja.lua:coruja.onUse]
- `Action()` assigned to `coruja` [actions_coruja.lua:coruja]
- `Action()` registration [actions_coruja.lua:Action]
- `glasshoneyfun.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_glasshoneyfun.lua:glasshoneyfun.onUse]
- `Action()` assigned to `glasshoneyfun` [actions_glasshoneyfun.lua:glasshoneyfun]
- `Action()` registration [actions_glasshoneyfun.lua:Action]
- `lyre.onUse(player, item, frompos, item2, topos)` [actions_lyre.lua:lyre.onUse]
- `Action()` assigned to `lyre` [actions_lyre.lua:lyre]
- `Action()` registration [actions_lyre.lua:Action]
- `peeler.onUse(player, item, frompos, item2, topos)` [actions_peeler.lua:peeler.onUse]
- `Action()` assigned to `peeler` [actions_peeler.lua:peeler]
- `Action()` registration [actions_peeler.lua:Action]
- `peelerfun.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_peelerfun.lua:peelerfun.onUse]
- `Action()` assigned to `peelerfun` [actions_peelerfun.lua:peelerfun]
- `Action()` registration [actions_peelerfun.lua:Action]
- `pickenchanted.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_pickenchanted.lua:pickenchanted.onUse]
- [1-fafnars-wrath](./1-fafnars-wrath/README.md) - Component package under `scripts/quests/kilmaresh_quest/1-fafnars-wrath` containing 4 files (`2-ambassadors-treason.lua`..`8-blessing-the-statues.lua`).

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_augerfun.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_basin.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_cagekey.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_coruja.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_glasshoneyfun.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lyre.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_peeler.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_peelerfun.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_pickenchanted.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_portal_minis_kilmaresh.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_portal_minis_kilmaresh.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_sangra.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_augerfun.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_augerfun.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_basin.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_basin.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_basin.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_cagekey.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_cagekey.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_cagekey.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_coruja.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_coruja.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_glasshoneyfun.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_glasshoneyfun.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
