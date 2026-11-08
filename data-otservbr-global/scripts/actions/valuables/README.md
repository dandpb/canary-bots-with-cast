# Valuables

## Overview
Component package under `scripts/actions/valuables` containing 1 files (`random_items.lua`..`random_items.lua`).

## Interface
- `randomItems.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [random_items.lua:randomItems.onUse]
- `Action()` assigned to `randomItems` [random_items.lua:randomItems]
- `Action()` registration [random_items.lua:Action]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [random_items.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [random_items.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
