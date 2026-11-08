# daily_reward

## Overview
Package implementation for `data/modules/scripts/daily_reward`, providing component logic and data interfaces for daily_reward.

## Interface
- `onRecvbyte` (`[daily_reward.lua:onRecvbyte]`)
- `Player.sendOpenRewardWall` (`[daily_reward.lua:Player.sendOpenRewardWall]`)
- `Player.sendCollectionResource` (`[daily_reward.lua:Player.sendCollectionResource]`)
- `Player.selectDailyReward` (`[daily_reward.lua:Player.selectDailyReward]`)
- `Player.sendError` (`[daily_reward.lua:Player.sendError]`)
- `Player.sendDailyRewardCollectionState` (`[daily_reward.lua:Player.sendDailyRewardCollectionState]`)
- `Player.sendRewardHistory` (`[daily_reward.lua:Player.sendRewardHistory]`)
- `Player.readDailyReward` (`[daily_reward.lua:Player.readDailyReward]`)

## Invariants
- None

## Side Effects
- Executes SQL queries against game database (`[daily_reward.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
