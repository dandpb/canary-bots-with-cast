# Tibia Tales

## Overview
Component package under `scripts/quests/tibia_tales` containing 1 files (`actions_ultimate_booze_beer_bottle.lua`..`actions_ultimate_booze_beer_bottle.lua`).

## Interface
- `ultimateBoozer.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ultimate_booze_beer_bottle.lua:ultimateBoozer.onUse]
- `Action()` assigned to `ultimateBoozer` [actions_ultimate_booze_beer_bottle.lua:ultimateBoozer]
- `Action()` registration [actions_ultimate_booze_beer_bottle.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ultimate_booze_beer_bottle.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ultimate_booze_beer_bottle.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_ultimate_booze_beer_bottle.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_ultimate_booze_beer_bottle.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
