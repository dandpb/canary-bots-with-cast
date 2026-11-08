# doors

## Overview
Package implementation for `data/scripts/actions/doors`, providing component logic and data interfaces for doors.

## Interface
- `customDoor.onUse` (`[custom_door.lua:customDoor.onUse]`)
- `keyDoor.onUse` (`[key_door.lua:keyDoor.onUse]`)
- `levelDoor.onUse` (`[level_door.lua:levelDoor.onUse]`)
- `questDoor.onUse` (`[quest_door.lua:questDoor.onUse]`)

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
