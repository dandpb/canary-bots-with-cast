# The Tainted Soul

## Overview
Component package under `scripts/quests/the_tainted_soul` containing 1 files (`actions_star_herb.lua`..`actions_star_herb.lua`).

## Interface
- `starHerb.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_star_herb.lua:starHerb.onUse]
- `Action()` assigned to `starHerb` [actions_star_herb.lua:starHerb]
- `Action()` registration [actions_star_herb.lua:Action]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_star_herb.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_star_herb.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
