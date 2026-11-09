# creaturescripts

## Overview
Package implementation for `data-canary/scripts/creaturescripts`, providing component logic and data interfaces for creaturescripts.

## Interface
- `dropLoot.onDeath` (`[drop_loot.lua:dropLoot.onDeath]`)
- `freeQuests.onLogin` (`[free_quest.lua:freeQuests.onLogin]`)

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[free_quest.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
