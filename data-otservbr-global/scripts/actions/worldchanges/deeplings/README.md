# Deeplings

## Overview
Component package under `scripts/actions/worldchanges/deeplings` containing 1 files (`bosses_reward.lua`..`bosses_reward.lua`).

## Interface
- `bossesReward.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [bosses_reward.lua:bossesReward.onUse]
- `Action()` assigned to `bossesReward` [bosses_reward.lua:bossesReward]
- `Action()` registration [bosses_reward.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [bosses_reward.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [bosses_reward.lua:register]
- Mutates player or global storage state via `setStorageValue` [bosses_reward.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [bosses_reward.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
