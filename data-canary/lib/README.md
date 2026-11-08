# Datapack Lua Library (`data-canary/lib`)

## Overview
Provides the top-level Lua library entrypoint (`lib.lua`) for the `data-canary` datapack.

## Interface
- `[lib.lua:2]` — Executes `dofile(DATA_DIRECTORY .. "/lib/core/load.lua")`.
- Subdirectories:
  - `core`: [`./core/README.md`](./core/README.md) — Core storage key definitions (`Storage`, `GlobalStorage`) and quest catalog loader.

## Invariants
- `[lib.lua:2]` requires global `DATA_DIRECTORY` to be set by the server runtime before `lib.lua` is executed.

## Side Effects
- `[lib.lua:2]` executes `data-canary/lib/core/load.lua`, registering global `Storage` and `GlobalStorage` tables and loading the quest catalog.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
