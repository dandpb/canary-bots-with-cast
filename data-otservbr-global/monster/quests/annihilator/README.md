# Annihilator

## Overview
Component package under `monster/quests/annihilator` containing 1 files (`angry_demon.lua`..`angry_demon.lua`).

## Interface
- `Game.createMonsterType("Angry Demon")` and `mType:register(monster)` [angry_demon.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [angry_demon.lua:monster.flags]

## Side Effects
- Registers monster type `Angry Demon` into the global `Game` engine registry via `mType:register(monster)` [angry_demon.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
