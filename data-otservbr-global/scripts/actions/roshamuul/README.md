# Roshamuul

## Overview
Intermediate blueprint grouping 1 subdirectories under `scripts/actions/roshamuul`.

## Subdirectories & Boundaries
- [prison](./prison/README.md) - Component package under `scripts/actions/roshamuul/prison` containing 2 files (`golden.lua`..`keys.lua`).

## Interface
- `golden.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [golden.lua:golden.onUse]
- `Action()` assigned to `golden` [golden.lua:golden]
- [prison](./prison/README.md) - Component package under `scripts/actions/roshamuul/prison` containing 2 files (`golden.lua`..`keys.lua`).

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [golden.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [golden.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
