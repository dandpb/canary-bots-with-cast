# systems

## Overview
Package implementation for `data/libs/systems`, providing component logic and data interfaces for systems.

## Interface
- `Player.getBlessings` (`[blessing.lua:Player.getBlessings]`)
- `Player.addMissingBless` (`[blessing.lua:Player.addMissingBless]`)
- `Blessings` (`[blessing.lua:Blessings]`)
- `Concoction.find` (`[concoctions.lua:Concoction.find]`)
- `Concoction.new` (`[concoctions.lua:Concoction.new]`)
- `Concoction.initAll` (`[concoctions.lua:Concoction.initAll]`)
- `Concoction.experienceTick` (`[concoctions.lua:Concoction.experienceTick]`)
- `Concoction:cooldown` (`[concoctions.lua:Concoction:cooldown]`)
- `Concoction:totalDuration` (`[concoctions.lua:Concoction:totalDuration]`)
- `Concoction:tickType` (`[concoctions.lua:Concoction:tickType]`)

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[concoctions.lua]`)
- Executes SQL queries against game database (`[daily_reward.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[daily_reward.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[encounters.lua]`)
- Executes SQL queries against game database (`[hireling.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[hireling.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
