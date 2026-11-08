# lib

## Overview
Package implementation for `data-canary/scripts/lib`, providing component logic and data interfaces for lib.

## Interface
- `destroyItem` (`[register_actions.lua:destroyItem]`)
- `onUseMachete` (`[register_actions.lua:onUseMachete]`)
- `onUsePick` (`[register_actions.lua:onUsePick]`)
- `onUseRope` (`[register_actions.lua:onUseRope]`)
- `onUseShovel` (`[register_actions.lua:onUseShovel]`)
- `onUseScythe` (`[register_actions.lua:onUseScythe]`)
- `onUseSickle` (`[register_actions.lua:onUseSickle]`)
- `onUseCrowbar` (`[register_actions.lua:onUseCrowbar]`)

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
