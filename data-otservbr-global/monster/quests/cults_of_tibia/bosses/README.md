# Bosses

## Overview
Provides 27 direct files (`dorokoll_the_mystic.lua`..`zarcorix_of_yalahar.lua`) and 2 subdirectories under `monster/quests/cults_of_tibia/bosses`.

## Interface
- Defines 27 script/configuration files (`dorokoll_the_mystic.lua` through `zarcorix_of_yalahar.lua`) [dorokoll_the_mystic.lua]
- `Game.createMonsterType("Dorokoll the Mystic")` and `mType:register(monster)` [dorokoll_the_mystic.lua:Game.createMonsterType]
- `Game.createMonsterType("Dorokoll The Mystic Stop")` and `mType:register(monster)` [dorokoll_the_mystic_stop.lua:Game.createMonsterType]
- `Game.createMonsterType("Eliz the Unyielding")` and `mType:register(monster)` [eliz_the_unyielding.lua:Game.createMonsterType]
- `Game.createMonsterType("Eliz The Unyielding Stop")` and `mType:register(monster)` [eliz_the_unyielding_stop.lua:Game.createMonsterType]
- `Game.createMonsterType("Eshtaba the Conjurer")` and `mType:register(monster)` [eshtaba_the_conjurer.lua:Game.createMonsterType]
- `Game.createMonsterType("Eshtaba The Conjurer Stop")` and `mType:register(monster)` [eshtaba_the_conjurer_stop.lua:Game.createMonsterType]
- `Game.createMonsterType("Essence of Malice")` and `mType:register(monster)` [essence_of_malice.lua:Game.createMonsterType]
- `Game.createMonsterType("Last Planegazer")` and `mType:register(monster)` [last_planegazer.lua:Game.createMonsterType]
- `Game.createMonsterType("Leiden")` and `mType:register(monster)` [leiden.lua:Game.createMonsterType]
- `Game.createMonsterType("Malkhar Deathbringer")` and `mType:register(monster)` [malkhar_deathbringer.lua:Game.createMonsterType]
- `Game.createMonsterType("Malkhar Deathbringer Stop")` and `mType:register(monster)` [malkhar_deathbringer_stop.lua:Game.createMonsterType]
- `Game.createMonsterType("Mezlon the Defiler")` and `mType:register(monster)` [mezlon_the_defiler.lua:Game.createMonsterType]
- `Game.createMonsterType("Mezlon The Defiler Stop")` and `mType:register(monster)` [mezlon_the_defiler_stop.lua:Game.createMonsterType]
- `Game.createMonsterType("Ravenous Hunger")` and `mType:register(monster)` [ravenous_hunger.lua:Game.createMonsterType]
- `Game.createMonsterType("The Armored Voidborn")` and `mType:register(monster)` [the_armored_voidborn.lua:Game.createMonsterType]
- `Game.createMonsterType("The Corruptor of Souls")` and `mType:register(monster)` [the_corruptor_of_souls.lua:Game.createMonsterType]
- `Game.createMonsterType("The False God")` and `mType:register(monster)` [the_false_god.lua:Game.createMonsterType]
- `Game.createMonsterType("The Remorseless Corruptor")` and `mType:register(monster)` [the_remorseless_corruptor.lua:Game.createMonsterType]
- `Game.createMonsterType("The Sandking")` and `mType:register(monster)` [the_sandking.lua:Game.createMonsterType]
- `Game.createMonsterType("The Sandking Fake")` and `mType:register(monster)` [the_sandking_fake.lua:Game.createMonsterType]
- `Game.createMonsterType("The Sinister Hermit")` and `mType:register(monster)` [the_sinister_hermit_clean.lua:Game.createMonsterType]
- `Game.createMonsterType("The Sinister Hermit Dirty")` and `mType:register(monster)` [the_sinister_hermit_dirty.lua:Game.createMonsterType]
- `Game.createMonsterType("The Souldespoiler")` and `mType:register(monster)` [the_souldespoiler.lua:Game.createMonsterType]
- `Game.createMonsterType("The Source of Corruption")` and `mType:register(monster)` [the_source_of_corruption.lua:Game.createMonsterType]
- [pillars](./pillars/README.md) - Component package under `monster/quests/cults_of_tibia/bosses/pillars` containing 7 files (`containment_crystal.lua`..`pillar_of_summoning.lua`).
- [summons](./summons/README.md) - Component package under `monster/quests/cults_of_tibia/bosses/summons` containing 13 files (`dark_soul.lua`..`voidshard.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dorokoll_the_mystic.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dorokoll_the_mystic_stop.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [eliz_the_unyielding.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [eliz_the_unyielding_stop.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [eshtaba_the_conjurer.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [eshtaba_the_conjurer_stop.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [essence_of_malice.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [last_planegazer.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [leiden.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [malkhar_deathbringer.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [malkhar_deathbringer_stop.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mezlon_the_defiler.lua:monster.flags]

## Side Effects
- Registers monster type `Dorokoll the Mystic` into the global `Game` engine registry via `mType:register(monster)` [dorokoll_the_mystic.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [dorokoll_the_mystic.lua:monster.events]
- Registers monster type `Dorokoll The Mystic Stop` into the global `Game` engine registry via `mType:register(monster)` [dorokoll_the_mystic_stop.lua:mType:register]
- Registers monster type `Eliz the Unyielding` into the global `Game` engine registry via `mType:register(monster)` [eliz_the_unyielding.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [eliz_the_unyielding.lua:monster.events]
- Registers monster type `Eliz The Unyielding Stop` into the global `Game` engine registry via `mType:register(monster)` [eliz_the_unyielding_stop.lua:mType:register]
- Registers monster type `Eshtaba the Conjurer` into the global `Game` engine registry via `mType:register(monster)` [eshtaba_the_conjurer.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [eshtaba_the_conjurer.lua:monster.events]
- Registers monster type `Eshtaba The Conjurer Stop` into the global `Game` engine registry via `mType:register(monster)` [eshtaba_the_conjurer_stop.lua:mType:register]
- Registers monster type `Essence of Malice` into the global `Game` engine registry via `mType:register(monster)` [essence_of_malice.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [essence_of_malice.lua:monster.events]
- Registers monster type `Last Planegazer` into the global `Game` engine registry via `mType:register(monster)` [last_planegazer.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
