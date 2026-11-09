# Cults Of Tibia

## Overview
Provides 28 direct files (`animated_clomp.lua`..`orc_cultist.lua`) and 1 subdirectories under `monster/quests/cults_of_tibia`.

## Interface
- Defines 28 script/configuration files (`animated_clomp.lua` through `orc_cultist.lua`) [animated_clomp.lua]
- `Game.createMonsterType("Animated Clomp")` and `mType:register(monster)` [animated_clomp.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Cyclops")` and `mType:register(monster)` [animated_cyclops.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Guzzlemaw")` and `mType:register(monster)` [animated_guzzlemaw.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Moohtant")` and `mType:register(monster)` [animated_moohtant.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Mummy")` and `mType:register(monster)` [animated_mummy.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Ogre Brute")` and `mType:register(monster)` [animated_ogre_brute.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Ogre Savage")` and `mType:register(monster)` [animated_ogre_savage.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Ogre Shaman")` and `mType:register(monster)` [animated_ogre_shaman.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Stone Rhino")` and `mType:register(monster)` [animated_rhino.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Rotworm")` and `mType:register(monster)` [animated_rotworm.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Skunk")` and `mType:register(monster)` [animated_skunk.lua:Game.createMonsterType]
- `Game.createMonsterType("Animated Stone Golem")` and `mType:register(monster)` [animated_stone_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Barkless Devotee")` and `mType:register(monster)` [barkless_devotee.lua:Game.createMonsterType]
- `Game.createMonsterType("Barkless Fanatic")` and `mType:register(monster)` [barkless_fanatic.lua:Game.createMonsterType]
- `Game.createMonsterType("Containment Machine")` and `mType:register(monster)` [containment_machine.lua:Game.createMonsterType]
- `Game.createMonsterType("Cult Believer")` and `mType:register(monster)` [cult_believer.lua:Game.createMonsterType]
- `Game.createMonsterType("Cult Enforcer")` and `mType:register(monster)` [cult_enforcer.lua:Game.createMonsterType]
- `Game.createMonsterType("Cult Scholar")` and `mType:register(monster)` [cult_scholar.lua:Game.createMonsterType]
- `Game.createMonsterType("Goldhanded Cultist")` and `mType:register(monster)` [goldhanded_cultist.lua:Game.createMonsterType]
- `Game.createMonsterType("Minotaur Idol")` and `mType:register(monster)` [minotaur_idol.lua:Game.createMonsterType]
- `Game.createMonsterType("Misguided Bully")` and `mType:register(monster)` [misguided_bully.lua:Game.createMonsterType]
- `Game.createMonsterType("Misguided Shadow")` and `mType:register(monster)` [misguided_shadow.lua:Game.createMonsterType]
- `Game.createMonsterType("Misguided Thief")` and `mType:register(monster)` [misguided_thief.lua:Game.createMonsterType]
- `Game.createMonsterType("Orc Cult Fanatic")` and `mType:register(monster)` [orc_cult_fanatic.lua:Game.createMonsterType]
- [bosses](./bosses/README.md) - Provides 27 direct files (`dorokoll_the_mystic.lua`..`zarcorix_of_yalahar.lua`) and 2 subdirectories under `monster/quests/cults_of_tibia/bosses`.

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_clomp.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_cyclops.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_guzzlemaw.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_moohtant.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_mummy.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_ogre_brute.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_ogre_savage.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_ogre_shaman.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_rhino.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_rotworm.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_skunk.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_stone_golem.lua:monster.flags]

## Side Effects
- Registers monster type `Animated Clomp` into the global `Game` engine registry via `mType:register(monster)` [animated_clomp.lua:mType:register]
- Registers monster type `Animated Cyclops` into the global `Game` engine registry via `mType:register(monster)` [animated_cyclops.lua:mType:register]
- Registers monster type `Animated Guzzlemaw` into the global `Game` engine registry via `mType:register(monster)` [animated_guzzlemaw.lua:mType:register]
- Registers monster type `Animated Moohtant` into the global `Game` engine registry via `mType:register(monster)` [animated_moohtant.lua:mType:register]
- Registers monster type `Animated Mummy` into the global `Game` engine registry via `mType:register(monster)` [animated_mummy.lua:mType:register]
- Registers monster type `Animated Ogre Brute` into the global `Game` engine registry via `mType:register(monster)` [animated_ogre_brute.lua:mType:register]
- Registers monster type `Animated Ogre Savage` into the global `Game` engine registry via `mType:register(monster)` [animated_ogre_savage.lua:mType:register]
- Registers monster type `Animated Ogre Shaman` into the global `Game` engine registry via `mType:register(monster)` [animated_ogre_shaman.lua:mType:register]
- Registers monster type `Animated Stone Rhino` into the global `Game` engine registry via `mType:register(monster)` [animated_rhino.lua:mType:register]
- Registers monster type `Animated Rotworm` into the global `Game` engine registry via `mType:register(monster)` [animated_rotworm.lua:mType:register]
- Registers monster type `Animated Skunk` into the global `Game` engine registry via `mType:register(monster)` [animated_skunk.lua:mType:register]
- Registers monster type `Animated Stone Golem` into the global `Game` engine registry via `mType:register(monster)` [animated_stone_golem.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
