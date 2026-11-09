# Slime Monsters (`data-canary/monster/slimes`)

## Overview
Defines and registers 2 slime `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[defiler.lua:mType]` — `Game.createMonsterType("Defiler")` (`health = 3650`, `experience = 3700`), registered via `mType:register(monster)`.
- `[slime.lua:mType]` — `Game.createMonsterType("Slime")` (`health = 150`, `experience = 160`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
