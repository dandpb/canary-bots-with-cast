# Summons

## Overview
Component package under `monster/quests/no_rest_for_the_wicked/summons` containing 1 files (`overcharged_demon.lua`..`overcharged_demon.lua`).

## Interface
- `Game.createMonsterType("Overcharged Demon")` and `mType:register(monster)` [overcharged_demon.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [overcharged_demon.lua:monster.flags]

## Side Effects
- Registers monster type `Overcharged Demon` into the global `Game` engine registry via `mType:register(monster)` [overcharged_demon.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
