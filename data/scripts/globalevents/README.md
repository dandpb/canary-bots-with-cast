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
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[bot_house_reclaim.lua]`)
- Executes SQL queries against game database (`[bot_manager.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[bot_manager.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[bot_market.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[bot_market_funding.lua]`)
- Executes SQL queries against game database (`[bot_test_commands.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
