# lib

## Overview
Package implementation for `data/modules/lib`, providing component logic and data interfaces for lib.

## Interface
- `addPlayerEvent` (`[modules.lua:addPlayerEvent]`)
- `Player.updateFightModes` (`[modules.lua:Player.updateFightModes]`)

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[modules.lua]`)

## Verification
- See the [Lua regression guide](../../../tests/lua/README.md).
