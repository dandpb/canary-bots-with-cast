# Humanoid Monsters (`data-canary/monster/humanoids`)

## Overview
Defines and registers 4 humanoid `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[frost_troll.lua:mType]` — `Game.createMonsterType("Frost Troll")` (`health = 55`, `experience = 23`), registered via `mType:register(monster)`.
- `[goblin.lua:mType]` — `Game.createMonsterType("Goblin")` (`health = 50`, `experience = 25`), registered via `mType:register(monster)`.
- `[island_troll.lua:mType]` — `Game.createMonsterType("Island Troll")` (`health = 50`, `experience = 20`), registered via `mType:register(monster)`.
- `[troll.lua:mType]` — `Game.createMonsterType("Troll")` (`health = 50`, `experience = 20`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
