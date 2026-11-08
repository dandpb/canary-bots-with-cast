# decay

## Overview
Package implementation for `src/items/decay`, providing component logic and data interfaces for decay.

## Interface
- `Item` (`[decay.hpp:Item]`)
- `Decay` (`[decay.hpp:Decay]`)
- `startDecay` (`[decay.hpp:startDecay]`)
- `stopDecay` (`[decay.hpp:stopDecay]`)
- `checkDecay` (`[decay.hpp:checkDecay]`)
- `internalDecayItem` (`[decay.hpp:internalDecayItem]`)

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[decay.cpp]`)
- Schedules timed tasks or dispatcher callbacks (`[decay.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
