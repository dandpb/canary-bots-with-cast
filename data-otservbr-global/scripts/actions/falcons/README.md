# Falcons

## Overview
Component package under `scripts/actions/falcons` containing 1 files (`falcon_shield.lua`..`falcon_shield.lua`).

## Interface
- `falconShield.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [falcon_shield.lua:falconShield.onUse]
- `Action()` assigned to `falconShield` [falcon_shield.lua:falconShield]
- `Action()` registration [falcon_shield.lua:Action]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [falcon_shield.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [falcon_shield.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
