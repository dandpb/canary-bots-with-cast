# Undead Monsters (`data-canary/monster/undeads`)

## Overview
Defines and registers 3 undead `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[ghoul.lua:mType]` — `Game.createMonsterType("Ghoul")` (`health = 100`, `experience = 85`), registered via `mType:register(monster)`.
- `[mummy.lua:mType]` — `Game.createMonsterType("Mummy")` (`health = 240`, `experience = 150`), registered via `mType:register(monster)`.
- `[skeleton.lua:mType]` — `Game.createMonsterType("Skeleton")` (`health = 50`, `experience = 35`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
