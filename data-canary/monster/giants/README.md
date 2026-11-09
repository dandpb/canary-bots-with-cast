# Giant Monsters (`data-canary/monster/giants`)

## Overview
Defines and registers 4 giant `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[behemoth.lua:mType]` — `Game.createMonsterType("Behemoth")` (`health = 4000`, `experience = 2500`), registered via `mType:register(monster)`.
- `[cyclops.lua:mType]` — `Game.createMonsterType("Cyclops")` (`health = 260`, `experience = 150`), registered via `mType:register(monster)`.
- `[cyclops_drone.lua:mType]` — `Game.createMonsterType("Cyclops Drone")` (`health = 325`, `experience = 200`), registered via `mType:register(monster)`.
- `[cyclops_smith.lua:mType]` — `Game.createMonsterType("Cyclops Smith")` (`health = 435`, `experience = 255`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
