# Farmine

## Overview
Component package under `scripts/actions/farmine` containing 1 files (`temple_of_equilibrium_vines.lua`..`temple_of_equilibrium_vines.lua`).

## Interface
- `templeOfEquilibriumVines.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [temple_of_equilibrium_vines.lua:templeOfEquilibriumVines.onUse]
- `Action()` assigned to `templeOfEquilibriumVines` [temple_of_equilibrium_vines.lua:templeOfEquilibriumVines]
- `Action()` registration [temple_of_equilibrium_vines.lua:Action]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [temple_of_equilibrium_vines.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [temple_of_equilibrium_vines.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
