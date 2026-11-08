# The Postman Missions Quest

## Overview
Component package under `scripts/quests/the_postman_missions_quest` containing 3 files (`actions_package.lua`..`actions_waldos_posthorn.lua`).

## Interface
- `postmanPackage.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_package.lua:postmanPackage.onUse]
- `Action()` assigned to `postmanPackage` [actions_package.lua:postmanPackage]
- `Action()` registration [actions_package.lua:Action]
- `postmanPresent.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_present.lua:postmanPresent.onUse]
- `Action()` assigned to `postmanPresent` [actions_present.lua:postmanPresent]
- `Action()` registration [actions_present.lua:Action]
- `postmanWaldos.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_waldos_posthorn.lua:postmanWaldos.onUse]
- `Action()` assigned to `postmanWaldos` [actions_waldos_posthorn.lua:postmanWaldos]
- `Action()` registration [actions_waldos_posthorn.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_package.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_waldos_posthorn.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_package.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_package.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_package.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_present.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_present.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_waldos_posthorn.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_waldos_posthorn.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_waldos_posthorn.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
