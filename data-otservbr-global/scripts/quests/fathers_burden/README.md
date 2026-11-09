# Fathers Burden

## Overview
Component package under `scripts/quests/fathers_burden` containing 1 files (`actions_corpse.lua`..`actions_corpse.lua`).

## Interface
- `fatherCorpse.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_corpse.lua:fatherCorpse.onUse]
- `Action()` assigned to `fatherCorpse` [actions_corpse.lua:fatherCorpse]
- `Action()` registration [actions_corpse.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_corpse.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_corpse.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_corpse.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_corpse.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
