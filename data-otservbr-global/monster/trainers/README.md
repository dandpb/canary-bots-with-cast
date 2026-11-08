# Trainers

## Overview
Component package under `monster/trainers` containing 1 files (`training_machine.lua`..`training_machine.lua`).

## Interface
- `Game.createMonsterType("Training Machine")` and `mType:register(monster)` [training_machine.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [training_machine.lua:monster.flags]

## Side Effects
- Registers monster type `Training Machine` into the global `Game` engine registry via `mType:register(monster)` [training_machine.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
