# Vermin Monsters (`data-canary/monster/vermins`)

## Overview
Defines and registers 4 vermin `MonsterType` definitions for the `data-canary` datapack.

## Interface
- `[poison_spider.lua:mType]` — `Game.createMonsterType("Poison Spider")` (`health = 26`, `experience = 22`), registered via `mType:register(monster)`.
- `[sandcrawler.lua:mType]` — `Game.createMonsterType("Sandcrawler")` (`health = 30`, `experience = 20`), registered via `mType:register(monster)`.
- `[spider.lua:mType]` — `Game.createMonsterType("Spider")` (`health = 20`, `experience = 12`), registered via `mType:register(monster)`.
- `[wasp.lua:mType]` — `Game.createMonsterType("Wasp")` (`health = 35`, `experience = 24`), registered via `mType:register(monster)`.

## Invariants
- None

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
