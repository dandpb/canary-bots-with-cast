# Vip

## Overview
Component package under `scripts/globalevents/vip` containing 2 files (`online_coins.lua`..`online_tokens.lua`).

## Interface
- `coinsPerRun(coinsPerHour)` [online_coins.lua:coinsPerRun]
- `onlineCoinsEvent.onThink(interval)` [online_coins.lua:onlineCoinsEvent.onThink]
- `GlobalEvent("GainCoinInterval")` assigned to `onlineCoinsEvent` [online_coins.lua:onlineCoinsEvent]
- `GlobalEvent("GainCoinInterval")` registration [online_coins.lua:GlobalEvent]
- `tokensPerRun(tokensPerHour)` [online_tokens.lua:tokensPerRun]
- `onlineTokensEvent.onThink(interval)` [online_tokens.lua:onlineTokensEvent.onThink]
- `GlobalEvent("GainTokenInterval")` assigned to `onlineTokensEvent` [online_tokens.lua:onlineTokensEvent]
- `GlobalEvent("GainTokenInterval")` registration [online_tokens.lua:GlobalEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [online_coins.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [online_tokens.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [online_coins.lua:register]
- Mutates player or global storage state via `setStorageValue` [online_coins.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [online_tokens.lua:register]
- Mutates player or global storage state via `setStorageValue` [online_tokens.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [online_tokens.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
