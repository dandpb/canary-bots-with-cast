# globalevents

## Overview
Package implementation for `data/scripts/globalevents`, providing component logic and data interfaces for globalevents.

## Interface
- `Hibernation.onThink` (`[bot_hibernation.lua:Hibernation.onThink]`)
- `botStates` (`[bot_hibernation.lua:botStates]`)
- `botHouseReclaim.onThink` (`[bot_house_reclaim.lua:botHouseReclaim.onThink]`)
- `botStartup.onStartup` (`[bot_manager.lua:botStartup.onStartup]`)
- `botManager.onThink` (`[bot_manager.lua:botManager.onThink]`)
- `botShutdown.onShutdown` (`[bot_manager.lua:botShutdown.onShutdown]`)
- `sellerPass.onThink` (`[bot_market.lua:sellerPass.onThink]`)
- `acceptPass.onThink` (`[bot_market.lua:acceptPass.onThink]`)
- `purgePass.onThink` (`[bot_market.lua:purgePass.onThink]`)
- `depthPass.onThink` (`[bot_market.lua:depthPass.onThink]`)

## Invariants
- `botStartup.onStartup` loads one bot per scheduled event, yielding to the dispatcher between loads with adaptive pacing bounded to `100..1000 ms` (`nextDelayMs = max(100, floor(nextDelayMs / 2), min(1000, pressureMs * 4))`), retries failed loads up to 3 attempts with a 1-second retry delay, reports `[BOT_BATCH]` progress and syncs `players_online` visibility every `50` bots and on completion, grants quest access before hibernation, and restores persisted states only after the final load attempt (`[bot_manager.lua:botStartup.onStartup]`).

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[bot_house_reclaim.lua]`)
- Executes SQL queries against game database (`[bot_manager.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[bot_manager.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[bot_market.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[bot_market_funding.lua]`)
- Executes SQL queries against game database (`[bot_test_commands.lua]`)

## Verification
- See the [Lua regression guide](../../../tests/lua/README.md).
