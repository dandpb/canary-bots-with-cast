# Alawars Vault

## Overview
Component package under `scripts/quests/alawars_vault` containing 1 files (`action-lever.lua`..`action-lever.lua`).

## Interface
- `lever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-lever.lua:lever.onUse]
- `Action()` assigned to `lever` [action-lever.lua:lever]
- `Action()` registration [action-lever.lua:Action]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action-lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-lever.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action-lever.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
