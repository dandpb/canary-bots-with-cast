# Marapur

## Overview
Component package under `monster/quests/marapur` containing 1 files (`timira_the_many-headed.lua`..`timira_the_many-headed.lua`).

## Interface
- `Game.createMonsterType("Timira the Many-Headed")` and `mType:register(monster)` [timira_the_many-headed.lua:Game.createMonsterType]
- `mType.onAppear` lifecycle callback [timira_the_many-headed.lua:mType.onAppear]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [timira_the_many-headed.lua:monster.flags]

## Side Effects
- Registers monster type `Timira the Many-Headed` into the global `Game` engine registry via `mType:register(monster)` [timira_the_many-headed.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
