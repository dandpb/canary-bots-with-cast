# Too Hot To Handle Quest

## Overview
Component package under `scripts/quests/too_hot_to_handle_quest` containing 1 files (`the_brainstealer.lua`..`the_brainstealer.lua`).

## Interface
- `BossLever(config)` assigned to `lever` [the_brainstealer.lua:lever]
- `BossLever(config)` registration [the_brainstealer.lua:BossLever]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [the_brainstealer.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
