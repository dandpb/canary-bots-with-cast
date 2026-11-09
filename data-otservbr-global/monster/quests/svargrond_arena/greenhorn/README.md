# Greenhorn

## Overview
Component package under `monster/quests/svargrond_arena/greenhorn` containing 10 files (`achad.lua`..`the_hairy_one.lua`).

## Interface
- `Game.createMonsterType("Achad")` and `mType:register(monster)` [achad.lua:Game.createMonsterType]
- `Game.createMonsterType("Axeitus Headbanger")` and `mType:register(monster)` [axeitus_headbanger.lua:Game.createMonsterType]
- `Game.createMonsterType("Bloodpaw")` and `mType:register(monster)` [bloodpaw.lua:Game.createMonsterType]
- `Game.createMonsterType("Bovinus")` and `mType:register(monster)` [bovinus.lua:Game.createMonsterType]
- `Game.createMonsterType("Colerian the Barbarian")` and `mType:register(monster)` [colerian_the_barbarian.lua:Game.createMonsterType]
- `Game.createMonsterType("Cursed Gladiator")` and `mType:register(monster)` [cursed_gladiator.lua:Game.createMonsterType]
- `Game.createMonsterType("Frostfur")` and `mType:register(monster)` [frostfur.lua:Game.createMonsterType]
- `Game.createMonsterType("Orcus the Cruel")` and `mType:register(monster)` [orcus_the_cruel.lua:Game.createMonsterType]
- `Game.createMonsterType("Rocky")` and `mType:register(monster)` [rocky.lua:Game.createMonsterType]
- `Game.createMonsterType("The Hairy One")` and `mType:register(monster)` [the_hairy_one.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [achad.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [axeitus_headbanger.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bloodpaw.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bovinus.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [colerian_the_barbarian.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cursed_gladiator.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [frostfur.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [orcus_the_cruel.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rocky.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_hairy_one.lua:monster.flags]

## Side Effects
- Registers monster type `Achad` into the global `Game` engine registry via `mType:register(monster)` [achad.lua:mType:register]
- Registers monster type `Axeitus Headbanger` into the global `Game` engine registry via `mType:register(monster)` [axeitus_headbanger.lua:mType:register]
- Registers monster type `Bloodpaw` into the global `Game` engine registry via `mType:register(monster)` [bloodpaw.lua:mType:register]
- Registers monster type `Bovinus` into the global `Game` engine registry via `mType:register(monster)` [bovinus.lua:mType:register]
- Registers monster type `Colerian the Barbarian` into the global `Game` engine registry via `mType:register(monster)` [colerian_the_barbarian.lua:mType:register]
- Registers monster type `Cursed Gladiator` into the global `Game` engine registry via `mType:register(monster)` [cursed_gladiator.lua:mType:register]
- Registers monster type `Frostfur` into the global `Game` engine registry via `mType:register(monster)` [frostfur.lua:mType:register]
- Registers monster type `Orcus the Cruel` into the global `Game` engine registry via `mType:register(monster)` [orcus_the_cruel.lua:mType:register]
- Registers monster type `Rocky` into the global `Game` engine registry via `mType:register(monster)` [rocky.lua:mType:register]
- Registers monster type `The Hairy One` into the global `Game` engine registry via `mType:register(monster)` [the_hairy_one.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
