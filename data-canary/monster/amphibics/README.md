# Amphibic Monsters (`data-canary/monster/amphibics`)

## Overview
Defines and registers 11 amphibic `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[azure_frog.lua:mType]` — `Game.createMonsterType("Azure Frog")` (`health = 60`, `experience = 20`), registered via `mType:register(monster)`.
- `[bog_frog.lua:mType]` — `Game.createMonsterType("Bog Frog")` (`health = 25`, `experience = 0`), registered via `mType:register(monster)`.
- `[coral_frog.lua:mType]` — `Game.createMonsterType("Coral Frog")` (`health = 60`, `experience = 20`), registered via `mType:register(monster)`.
- `[crimson_frog.lua:mType]` — `Game.createMonsterType("Crimson Frog")` (`health = 60`, `experience = 20`), registered via `mType:register(monster)`.
- `[deathspawn.lua:mType]` — `Game.createMonsterType("Deathspawn")` (`health = 225`, `experience = 20`), registered via `mType:register(monster)`.
- `[filth_toad.lua:mType]` — `Game.createMonsterType("Filth Toad")` (`health = 185`, `experience = 90`), registered via `mType:register(monster)`.
- `[green_frog.lua:mType]` — `Game.createMonsterType("Green Frog")` (`health = 25`, `experience = 0`), registered via `mType:register(monster)`.
- `[infernal_frog.lua:mType]` — `Game.createMonsterType("Infernal Frog")` (`health = 655`, `experience = 190`), registered via `mType:register(monster)`.
- `[orchid_frog.lua:mType]` — `Game.createMonsterType("Orchid Frog")` (`health = 60`, `experience = 20`), registered via `mType:register(monster)`.
- `[salamander.lua:mType]` — `Game.createMonsterType("Salamander")` (`health = 70`, `experience = 25`), registered via `mType:register(monster)`.
- `[toad.lua:mType]` — `Game.createMonsterType("Toad")` (`health = 135`, `experience = 60`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
