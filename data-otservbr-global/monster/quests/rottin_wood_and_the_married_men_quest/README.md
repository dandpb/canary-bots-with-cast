# Rottin Wood And The Married Men Quest

## Overview
Component package under `monster/quests/rottin_wood_and_the_married_men_quest` containing 1 files (`travelling_merchant.lua`..`travelling_merchant.lua`).

## Interface
- `Game.createMonsterType("Travelling Merchant")` and `mType:register(monster)` [travelling_merchant.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [travelling_merchant.lua:monster.flags]

## Side Effects
- Registers monster type `Travelling Merchant` into the global `Game` engine registry via `mType:register(monster)` [travelling_merchant.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
