# Mounts

## Overview
Component package under `scripts/actions/mounts` containing 1 files (`mounts.lua`..`mounts.lua`).

## Interface
- `doFailAction(cid, mount, pos, item, itemEx, loseItem)` [mounts.lua:doFailAction]
- `mounts.onUse(cid, item, fromPosition, itemEx, toPosition)` [mounts.lua:mounts.onUse]
- `Action()` assigned to `mounts` [mounts.lua:mounts]
- `Action()` registration [mounts.lua:Action]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [mounts.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [mounts.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
