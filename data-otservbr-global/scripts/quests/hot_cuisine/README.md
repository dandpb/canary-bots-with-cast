# Hot Cuisine

## Overview
Component package under `scripts/quests/hot_cuisine` containing 2 files (`actions_cookbook1.lua`..`actions_cookbook2.lua`).

## Interface
- `hotCuisineCook1.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_cookbook1.lua:hotCuisineCook1.onUse]
- `Action()` assigned to `hotCuisineCook1` [actions_cookbook1.lua:hotCuisineCook1]
- `Action()` registration [actions_cookbook1.lua:Action]
- `hotCuisineCook2.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_cookbook2.lua:hotCuisineCook2.onUse]
- `Action()` assigned to `hotCuisineCook2` [actions_cookbook2.lua:hotCuisineCook2]
- `Action()` registration [actions_cookbook2.lua:Action]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_cookbook1.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_cookbook2.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
