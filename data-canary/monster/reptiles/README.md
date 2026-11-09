# Reptile Monsters (`data-canary/monster/reptiles`)

## Overview
Defines and registers 3 reptile `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[crocodile.lua:mType]` — `Game.createMonsterType("Crocodile")` (`health = 105`, `experience = 40`), registered via `mType:register(monster)`.
- `[snake.lua:mType]` — `Game.createMonsterType("Snake")` (`health = 15`, `experience = 10`), registered via `mType:register(monster)`.
- `[tortoise.lua:mType]` — `Game.createMonsterType("Tortoise")` (`health = 185`, `experience = 90`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
