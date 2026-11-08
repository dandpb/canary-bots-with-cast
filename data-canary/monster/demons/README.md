# Demon Monsters (`data-canary/monster/demons`)

## Overview
Defines and registers 6 demon `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[demon.lua:mType]` — `Game.createMonsterType("Demon")` (`health = 8200`, `experience = 6000`), registered via `mType:register(monster)`.
- `[destroyer.lua:mType]` — `Game.createMonsterType("Destroyer")` (`health = 3700`, `experience = 2500`), registered via `mType:register(monster)`.
- `[fury.lua:mType]` — `Game.createMonsterType("Fury")` (`health = 4100`, `experience = 4000`), registered via `mType:register(monster)`.
- `[hellhound.lua:mType]` — `Game.createMonsterType("Hellhound")` (`health = 7500`, `experience = 5440`), registered via `mType:register(monster)`.
- `[hellspawn.lua:mType]` — `Game.createMonsterType("Hellspawn")` (`health = 3500`, `experience = 2550`), registered via `mType:register(monster)`.
- `[juggernaut.lua:mType]` — `Game.createMonsterType("Juggernaut")` (`health = 18000`, `experience = 11200`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
