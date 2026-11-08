# Dragon Monsters (`data-canary/monster/dragons`)

## Overview
Defines and registers 5 dragon `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[dragon.lua:mType]` — `Game.createMonsterType("Dragon")` (`health = 1000`, `experience = 700`), registered via `mType:register(monster)`.
- `[dragon_lord.lua:mType]` — `Game.createMonsterType("Dragon Lord")` (`health = 1900`, `experience = 2100`), registered via `mType:register(monster)`.
- `[hydra.lua:mType]` — `Game.createMonsterType("Hydra")` (`health = 2350`, `experience = 2100`), registered via `mType:register(monster)`.
- `[ice_dragon.lua:mType]` — `Game.createMonsterType("Ice Dragon")` (`health = 2500`, `experience = 2300`), registered via `mType:register(monster)`.
- `[wyrm.lua:mType]` — `Game.createMonsterType("Wyrm")` (`health = 1825`, `experience = 1550`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
