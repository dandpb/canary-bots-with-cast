# Human Monsters (`data-canary/monster/humans`)

## Overview
Defines and registers 6 human `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[amazon.lua:mType]` — `Game.createMonsterType("Amazon")` (`health = 110`, `experience = 60`), registered via `mType:register(monster)`.
- `[assassin.lua:mType]` — `Game.createMonsterType("Assassin")` (`health = 175`, `experience = 105`), registered via `mType:register(monster)`.
- `[bandit.lua:mType]` — `Game.createMonsterType("Bandit")` (`health = 245`, `experience = 65`), registered via `mType:register(monster)`.
- `[hunter.lua:mType]` — `Game.createMonsterType("Hunter")` (`health = 150`, `experience = 150`), registered via `mType:register(monster)`.
- `[monk.lua:mType]` — `Game.createMonsterType("Monk")` (`health = 240`, `experience = 200`), registered via `mType:register(monster)`.
- `[valkyrie.lua:mType]` — `Game.createMonsterType("Valkyrie")` (`health = 190`, `experience = 85`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
