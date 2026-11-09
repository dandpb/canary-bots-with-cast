# System

## Overview
Component package under `scripts/actions/system` containing 1 files (`quest_reward_common.lua`..`quest_reward_common.lua`).

## Interface
- `playerAddItem(params, item, rewardIndex)` [quest_reward_common.lua:playerAddItem]
- `playerAddContainerItem(params, item, rewardIndex)` [quest_reward_common.lua:playerAddContainerItem]
- `questReward.onUse(player, item, fromPosition, itemEx, toPosition)` [quest_reward_common.lua:questReward.onUse]
- `Action()` assigned to `questReward` [quest_reward_common.lua:questReward]
- `Action()` registration [quest_reward_common.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [quest_reward_common.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [quest_reward_common.lua:register]
- Mutates player or global storage state via `setStorageValue` [quest_reward_common.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [quest_reward_common.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
