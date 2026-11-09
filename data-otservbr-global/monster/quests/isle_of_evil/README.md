# Isle Of Evil

## Overview
Component package under `monster/quests/isle_of_evil` containing 6 files (`boogey.lua`..`monstor.lua`).

## Interface
- `Game.createMonsterType("Boogey")` and `mType:register(monster)` [boogey.lua:Game.createMonsterType]
- `Game.createMonsterType("Dirtbeard")` and `mType:register(monster)` [dirtbeard.lua:Game.createMonsterType]
- `Game.createMonsterType("Doctor Perhaps")` and `mType:register(monster)` [doctor_perhaps.lua:Game.createMonsterType]
- `Game.createMonsterType("Evil Mastermind")` and `mType:register(monster)` [evil_mastermind.lua:Game.createMonsterType]
- `Game.createMonsterType("Mephiles")` and `mType:register(monster)` [mephiles.lua:Game.createMonsterType]
- `Game.createMonsterType("Monstor")` and `mType:register(monster)` [monstor.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [boogey.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dirtbeard.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [doctor_perhaps.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [evil_mastermind.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mephiles.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [monstor.lua:monster.flags]

## Side Effects
- Registers monster type `Boogey` into the global `Game` engine registry via `mType:register(monster)` [boogey.lua:mType:register]
- Registers monster type `Dirtbeard` into the global `Game` engine registry via `mType:register(monster)` [dirtbeard.lua:mType:register]
- Registers monster type `Doctor Perhaps` into the global `Game` engine registry via `mType:register(monster)` [doctor_perhaps.lua:mType:register]
- Registers monster type `Evil Mastermind` into the global `Game` engine registry via `mType:register(monster)` [evil_mastermind.lua:mType:register]
- Registers monster type `Mephiles` into the global `Game` engine registry via `mType:register(monster)` [mephiles.lua:mType:register]
- Registers monster type `Monstor` into the global `Game` engine registry via `mType:register(monster)` [monstor.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
