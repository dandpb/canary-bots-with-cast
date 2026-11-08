# Talkactions

## Overview
Intermediate blueprint grouping 1 subdirectories under `scripts/talkactions`.

## Subdirectories & Boundaries
- [god](./god/README.md) - Component package under `scripts/talkactions/god` containing 3 files (`house_backfill.lua`..`house_ingest.lua`).

## Interface
- `loadConfig()` [house_backfill.lua:loadConfig]
- `buildBotPool()` [house_backfill.lua:buildBotPool]
- [god](./god/README.md) - Component package under `scripts/talkactions/god` containing 3 files (`house_backfill.lua`..`house_ingest.lua`).

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [house_backfill.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [house_backfill.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
