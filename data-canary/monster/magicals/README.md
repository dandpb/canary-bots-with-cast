# Magical Monsters (`data-canary/monster/magicals`)

## Overview
Defines and registers 2 magical `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[frazzlemaw.lua:mType]` — `Game.createMonsterType("Frazzlemaw")` (`health = 4100`, `experience = 3740`), registered via `mType:register(monster)`.
- `[guzzlemaw.lua:mType]` — `Game.createMonsterType("Guzzlemaw")` (`health = 6400`, `experience = 6050`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
