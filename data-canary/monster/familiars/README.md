# Familiar Monsters (`data-canary/monster/familiars`)

## Overview
Defines and registers the 4 vocation summon familiar `MonsterType` definitions (`experience = 0`) for the `data-canary` datapack.

## Interface
- `[druid_familiar.lua:mType]` — `Game.createMonsterType("Druid familiar")` (`health = 20000`, `experience = 0`), registered via `mType:register(monster)`.
- `[knight_familiar.lua:mType]` — `Game.createMonsterType("Knight familiar")` (`health = 10000`, `experience = 0`), registered via `mType:register(monster)`.
- `[paladin_familiar.lua:mType]` — `Game.createMonsterType("Paladin familiar")` (`health = 15000`, `experience = 0`), registered via `mType:register(monster)`.
- `[sorcerer_familiar.lua:mType]` — `Game.createMonsterType("Sorcerer familiar")` (`health = 20000`, `experience = 0`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its familiar `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
