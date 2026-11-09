# Trainer Monster (`data-canary/monster/trainer`)

## Overview
Defines and registers the stationary `"Training Machine"` sparring `MonsterType` (`training_machine.lua`) for the `data-canary` datapack.

## Interface
- `[training_machine.lua:mType]` — `Game.createMonsterType("Training Machine")` (`health = 1000000`, `experience = 0`, `speed = 0`, `corpse = 0`), registered via `mType:register(monster)`.

## Invariants
- `[training_machine.lua:14]` sets `monster.speed = 0`, `monster.experience = 0`, `monster.corpse = 0`, and `monster.changeTarget.chance = 0` so the training dummy remains stationary, awards no experience or corpse, and does not switch targets.

## Side Effects
- `[training_machine.lua:76]` registers `"Training Machine"` in the global `MonsterType` registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
