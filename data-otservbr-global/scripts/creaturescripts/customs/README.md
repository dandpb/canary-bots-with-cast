# Customs

## Overview
Component package under `scripts/creaturescripts/customs` containing 2 files (`freequests.lua`..`reward_exercise.lua`).

## Interface
- `playerFreeQuestStart(playerId, index)` [freequests.lua:playerFreeQuestStart]
- `freeQuests.onLogin(player)` [freequests.lua:freeQuests.onLogin]
- `CreatureEvent("FreeQuests")` assigned to `freeQuests` [freequests.lua:freeQuests]
- `CreatureEvent("FreeQuests")` registration [freequests.lua:CreatureEvent]
- `winReward.onLogin(player)` [reward_exercise.lua:winReward.onLogin]
- `CreatureEvent("WinReward")` assigned to `winReward` [reward_exercise.lua:winReward]
- `CreatureEvent("WinReward")` registration [reward_exercise.lua:CreatureEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [freequests.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [reward_exercise.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [freequests.lua:register]
- Mutates player or global storage state via `setStorageValue` [freequests.lua:setStorageValue]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [freequests.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [reward_exercise.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
