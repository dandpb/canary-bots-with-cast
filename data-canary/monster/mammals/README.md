# Mammal Monsters (`data-canary/monster/mammals`)

## Overview
Defines and registers 4 mammal `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[bat.lua:mType]` — `Game.createMonsterType("Bat")` (`health = 30`, `experience = 10`), registered via `mType:register(monster)`.
- `[cave_rat.lua:mType]` — `Game.createMonsterType("Cave Rat")` (`health = 30`, `experience = 10`), registered via `mType:register(monster)`.
- `[winter_wolf.lua:mType]` — `Game.createMonsterType("Winter Wolf")` (`health = 30`, `experience = 20`), registered via `mType:register(monster)`.
- `[wolf.lua:mType]` — `Game.createMonsterType("Wolf")` (`health = 25`, `experience = 18`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
