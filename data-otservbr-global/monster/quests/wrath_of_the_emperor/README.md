# Wrath Of The Emperor

## Overview
Component package under `monster/quests/wrath_of_the_emperor` containing 9 files (`fury_of_the_emperor.lua`..`wrath_of_the_emperor.lua`).

## Interface
- `Game.createMonsterType("Fury of the Emperor")` and `mType:register(monster)` [fury_of_the_emperor.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard Abomination")` and `mType:register(monster)` [lizard_abomination.lua:Game.createMonsterType]
- `Game.createMonsterType("Mutated Zalamon")` and `mType:register(monster)` [mutated_zalamon.lua:Game.createMonsterType]
- `Game.createMonsterType("Scorn of the Emperor")` and `mType:register(monster)` [scorn_of_the_emperor.lua:Game.createMonsterType]
- `Game.createMonsterType("Snake God Essence")` and `mType:register(monster)` [snake_god_essence.lua:Game.createMonsterType]
- `Game.createMonsterType("Snake Thing")` and `mType:register(monster)` [snake_thing.lua:Game.createMonsterType]
- `Game.createMonsterType("Spite of the Emperor")` and `mType:register(monster)` [spite_of_the_emperor.lua:Game.createMonsterType]
- `Game.createMonsterType("The Keeper")` and `mType:register(monster)` [the_keeper.lua:Game.createMonsterType]
- `Game.createMonsterType("Wrath of the Emperor")` and `mType:register(monster)` [wrath_of_the_emperor.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fury_of_the_emperor.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lizard_abomination.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mutated_zalamon.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [scorn_of_the_emperor.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [snake_god_essence.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [snake_thing.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [spite_of_the_emperor.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_keeper.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [wrath_of_the_emperor.lua:monster.flags]

## Side Effects
- Registers monster type `Fury of the Emperor` into the global `Game` engine registry via `mType:register(monster)` [fury_of_the_emperor.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [fury_of_the_emperor.lua:monster.events]
- Registers monster type `Lizard Abomination` into the global `Game` engine registry via `mType:register(monster)` [lizard_abomination.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [lizard_abomination.lua:monster.events]
- Registers monster type `Mutated Zalamon` into the global `Game` engine registry via `mType:register(monster)` [mutated_zalamon.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [mutated_zalamon.lua:monster.events]
- Registers monster type `Scorn of the Emperor` into the global `Game` engine registry via `mType:register(monster)` [scorn_of_the_emperor.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [scorn_of_the_emperor.lua:monster.events]
- Registers monster type `Snake God Essence` into the global `Game` engine registry via `mType:register(monster)` [snake_god_essence.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [snake_god_essence.lua:monster.events]
- Registers monster type `Snake Thing` into the global `Game` engine registry via `mType:register(monster)` [snake_thing.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [snake_thing.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
