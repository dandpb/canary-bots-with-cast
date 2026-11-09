# The Powder Of The Stars

## Overview
Component package under `scripts/quests/oramond/the_powder_of_the_stars` containing 1 files (`actions_blue_pollen.lua`..`actions_blue_pollen.lua`).

## Interface
- `revertItem(toPosition, getItemId, itemTransform)` [actions_blue_pollen.lua:revertItem]
- `itemTransformation.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_blue_pollen.lua:itemTransformation.onUse]
- `Action()` assigned to `itemTransformation` [actions_blue_pollen.lua:itemTransformation]
- `Action()` registration [actions_blue_pollen.lua:Action]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_blue_pollen.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_blue_pollen.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_blue_pollen.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_blue_pollen.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
