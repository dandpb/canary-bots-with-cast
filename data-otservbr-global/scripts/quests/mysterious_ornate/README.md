# Mysterious Ornate

## Overview
Component package under `scripts/quests/mysterious_ornate` containing 1 files (`actions_mysterious_metal_egg.lua`..`actions_mysterious_metal_egg.lua`).

## Interface
- `mysterious.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mysterious_metal_egg.lua:mysterious.onUse]
- `Action()` assigned to `mysterious` [actions_mysterious_metal_egg.lua:mysterious]
- `Action()` registration [actions_mysterious_metal_egg.lua:Action]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mysterious_metal_egg.lua:register]

## Verification
- See the [Lua regression guide](../../../../tests/lua/README.md).
