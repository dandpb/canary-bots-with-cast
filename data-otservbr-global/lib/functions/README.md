# Functions

## Overview
Component package under `lib/functions` containing 2 files (`load.lua`..`players.lua`).

## Interface
- `dofile(DATA_DIRECTORY .. "/lib/functions/players.lua")` module loader [load.lua:dofile]
- `Player.getCookiesDelivered(self)` [players.lua:Player.getCookiesDelivered]
- `Player.checkGnomeRank(self)` [players.lua:Player.checkGnomeRank]
- `Player.addFamePoint(self)` [players.lua:Player.addFamePoint]
- `Player.getFamePoints(self)` [players.lua:Player.getFamePoints]
- `Player.removeFamePoints(self, amount)` [players.lua:Player.removeFamePoints]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [players.lua:getStorageValue]

## Side Effects
- Loads and executes `DATA_DIRECTORY .. "/lib/functions/players.lua"` via `dofile` [load.lua:dofile]
- Mutates player or global storage state via `setStorageValue` [players.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
