# Monster

## Overview
Intermediate blueprint grouping 30 subdirectories under `monster`.

## Subdirectories & Boundaries
- [amphibics](./amphibics/README.md) - Component package under `monster/amphibics` containing 12 files (`azure_frog.lua`..`toad.lua`).
- [aquatics](./aquatics/README.md) - Component package under `monster/aquatics` containing 40 files (`abyssal_calamary.lua`..`shark.lua`).
- [birds](./birds/README.md) - Component package under `monster/birds` containing 17 files (`agressive_chicken.lua`..`terror_bird.lua`).
- [bosses](./bosses/README.md) - Component package under `monster/bosses` containing 94 files (`alchemist_container.lua`..`zushuka.lua`).
- [constructs](./constructs/README.md) - Component package under `monster/constructs` containing 31 files (`animated_snowman.lua`..`worker_golem.lua`).
- [dawnport](./dawnport/README.md) - Component package under `monster/dawnport` containing 20 files (`brittle_skeleton.lua`..`woodling.lua`).
- [demons](./demons/README.md) - Component package under `monster/demons` containing 39 files (`askarak_demon.lua`..`vexclaw.lua`).
- [dragons](./dragons/README.md) - Component package under `monster/dragons` containing 17 files (`dragolisk.lua`..`wyrm.lua`).
- [elementals](./elementals/README.md) - Component package under `monster/elementals` containing 19 files (`candy_floss_elemental.lua`..`water_elemental.lua`).
- [event_creatures](./event_creatures/README.md) - Provides 14 direct files (`bones.lua`..`undead_minion.lua`) and 1 subdirectories under `monster/event_creatures`.
- [extra_dimensional](./extra_dimensional/README.md) - Component package under `monster/extra_dimensional` containing 11 files (`breach_brood.lua`..`yielothax.lua`).
- [familiars](./familiars/README.md) - Component package under `monster/familiars` containing 5 files (`druid_familiar.lua`..`sorcerer_familiar.lua`).
- [fey](./fey/README.md) - Component package under `monster/fey` containing 19 files (`angry_sugar_fairy.lua`..`wisp.lua`).
- [giants](./giants/README.md) - Component package under `monster/giants` containing 16 files (`beast_hulking_prehemoth.lua`..`orclops_ravager.lua`).
- [humanoids](./humanoids/README.md) - Component package under `monster/humanoids` containing 89 files (`broken_shaper.lua`..`young_troll.lua`).
- [humans](./humans/README.md) - Component package under `monster/humans` containing 75 files (`acolyte_of_darkness.lua`..`witch.lua`).
- [lycanthropes](./lycanthropes/README.md) - Component package under `monster/lycanthropes` containing 15 files (`cunning_werepanther.lua`..`white_weretiger.lua`).
- [magicals](./magicals/README.md) - Component package under `monster/magicals` containing 64 files (`animated_feather.lua`..`weakened_frazzlemaw.lua`).
- [mammals](./mammals/README.md) - Component package under `monster/mammals` containing 80 files (`badger.lua`..`yeti.lua`).
- [nostalgia](./nostalgia/README.md) - Component package under `monster/nostalgia` containing 8 files (`old_bear.lua`..`old_wolf.lua`).
- [plants](./plants/README.md) - Component package under `monster/plants` containing 15 files (`bane_bringer.lua`..`wilting_leaf_golem.lua`).
- [quests](./quests/README.md) - Intermediate blueprint grouping 43 subdirectories under `monster/quests`.
- [raids](./raids/README.md) - Component package under `monster/raids` containing 55 files (`arachir_the_ancient_one.lua`..`zulazza_the_corruptor.lua`).
- [reptiles](./reptiles/README.md) - Component package under `monster/reptiles` containing 42 files (`adult_goanna.lua`..`young_sea_serpent.lua`).
- [slimes](./slimes/README.md) - Component package under `monster/slimes` containing 12 files (`acid_blob.lua`..`squidgy_slime.lua`).
- [trainers](./trainers/README.md) - Component package under `monster/trainers` containing 1 files (`training_machine.lua`..`training_machine.lua`).
- [traps](./traps/README.md) - Component package under `monster/traps` containing 13 files (`deathslicer.lua`..`plaguethrower.lua`).
- [undeads](./undeads/README.md) - Component package under `monster/undeads` containing 63 files (`ahau.lua`..`zombie.lua`).
- [vermins](./vermins/README.md) - Component package under `monster/vermins` containing 62 files (`afflicted_strider.lua`..`wiggler.lua`).
- [wild_magics](./wild_magics/README.md) - Component package under `monster/wild_magics` containing 4 files (`wild_fire_magic.lua`..`wild_water_magic.lua`).

## Interface
- `Game.createMonsterType("Azure Frog")` and `mType:register(monster)` [azure_frog.lua:Game.createMonsterType]
- `Game.createMonsterType("Bog Frog")` and `mType:register(monster)` [bog_frog.lua:Game.createMonsterType]
- Defines 40 script/configuration files (`abyssal_calamary.lua` through `shark.lua`) [abyssal_calamary.lua]
- `Game.createMonsterType("Abyssal Calamary")` and `mType:register(monster)` [abyssal_calamary.lua:Game.createMonsterType]
- `Game.createMonsterType("Agressive Chicken")` and `mType:register(monster)` [agressive_chicken.lua:Game.createMonsterType]
- `Game.createMonsterType("Agrestic Chicken")` and `mType:register(monster)` [agrestic_chicken.lua:Game.createMonsterType]
- Defines 94 script/configuration files (`alchemist_container.lua` through `zushuka.lua`) [alchemist_container.lua]
- `Game.createMonsterType("Alchemist Container")` and `mType:register(monster)` [alchemist_container.lua:Game.createMonsterType]
- Defines 31 script/configuration files (`animated_snowman.lua` through `worker_golem.lua`) [animated_snowman.lua]
- `Game.createMonsterType("Animated Snowman")` and `mType:register(monster)` [animated_snowman.lua:Game.createMonsterType]
- `Game.createMonsterType("Brittle Skeleton")` and `mType:register(monster)` [brittle_skeleton.lua:Game.createMonsterType]
- `Game.createMonsterType("Crazed Dwarf")` and `mType:register(monster)` [crazed_dwarf.lua:Game.createMonsterType]
- Defines 39 script/configuration files (`askarak_demon.lua` through `vexclaw.lua`) [askarak_demon.lua]
- `Game.createMonsterType("Askarak Demon")` and `mType:register(monster)` [askarak_demon.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragolisk")` and `mType:register(monster)` [dragolisk.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragon")` and `mType:register(monster)` [dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Candy Floss Elemental")` and `mType:register(monster)` [candy_floss_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Cliff Strider")` and `mType:register(monster)` [cliff_strider.lua:Game.createMonsterType]
- `Game.createMonsterType("Bones")` and `mType:register(monster)` [bones.lua:Game.createMonsterType]
- `Game.createMonsterType("Eclipse Knight")` and `mType:register(monster)` [eclipse_knight.lua:Game.createMonsterType]
- `Game.createMonsterType("Breach Brood")` and `mType:register(monster)` [breach_brood.lua:Game.createMonsterType]
- `Game.createMonsterType("Dread Intruder")` and `mType:register(monster)` [dread_intruder.lua:Game.createMonsterType]
- `Game.createMonsterType("Druid familiar")` and `mType:register(monster)` [druid_familiar.lua:Game.createMonsterType]
- `Game.createMonsterType("Knight familiar")` and `mType:register(monster)` [knight_familiar.lua:Game.createMonsterType]
- `Game.createMonsterType("Angry Sugar Fairy")` and `mType:register(monster)` [angry_sugar_fairy.lua:Game.createMonsterType]
- [amphibics](./amphibics/README.md) - Component package under `monster/amphibics` containing 12 files (`azure_frog.lua`..`toad.lua`).
- [aquatics](./aquatics/README.md) - Component package under `monster/aquatics` containing 40 files (`abyssal_calamary.lua`..`shark.lua`).
- [birds](./birds/README.md) - Component package under `monster/birds` containing 17 files (`agressive_chicken.lua`..`terror_bird.lua`).
- [bosses](./bosses/README.md) - Component package under `monster/bosses` containing 94 files (`alchemist_container.lua`..`zushuka.lua`).
- [constructs](./constructs/README.md) - Component package under `monster/constructs` containing 31 files (`animated_snowman.lua`..`worker_golem.lua`).
- [dawnport](./dawnport/README.md) - Component package under `monster/dawnport` containing 20 files (`brittle_skeleton.lua`..`woodling.lua`).
- [demons](./demons/README.md) - Component package under `monster/demons` containing 39 files (`askarak_demon.lua`..`vexclaw.lua`).
- [dragons](./dragons/README.md) - Component package under `monster/dragons` containing 17 files (`dragolisk.lua`..`wyrm.lua`).
- [elementals](./elementals/README.md) - Component package under `monster/elementals` containing 19 files (`candy_floss_elemental.lua`..`water_elemental.lua`).
- [event_creatures](./event_creatures/README.md) - Provides 14 direct files (`bones.lua`..`undead_minion.lua`) and 1 subdirectories under `monster/event_creatures`.
- [extra_dimensional](./extra_dimensional/README.md) - Component package under `monster/extra_dimensional` containing 11 files (`breach_brood.lua`..`yielothax.lua`).
- [familiars](./familiars/README.md) - Component package under `monster/familiars` containing 5 files (`druid_familiar.lua`..`sorcerer_familiar.lua`).
- [fey](./fey/README.md) - Component package under `monster/fey` containing 19 files (`angry_sugar_fairy.lua`..`wisp.lua`).
- [giants](./giants/README.md) - Component package under `monster/giants` containing 16 files (`beast_hulking_prehemoth.lua`..`orclops_ravager.lua`).
- [humanoids](./humanoids/README.md) - Component package under `monster/humanoids` containing 89 files (`broken_shaper.lua`..`young_troll.lua`).
- [humans](./humans/README.md) - Component package under `monster/humans` containing 75 files (`acolyte_of_darkness.lua`..`witch.lua`).
- [lycanthropes](./lycanthropes/README.md) - Component package under `monster/lycanthropes` containing 15 files (`cunning_werepanther.lua`..`white_weretiger.lua`).
- [magicals](./magicals/README.md) - Component package under `monster/magicals` containing 64 files (`animated_feather.lua`..`weakened_frazzlemaw.lua`).
- [mammals](./mammals/README.md) - Component package under `monster/mammals` containing 80 files (`badger.lua`..`yeti.lua`).
- [nostalgia](./nostalgia/README.md) - Component package under `monster/nostalgia` containing 8 files (`old_bear.lua`..`old_wolf.lua`).
- [plants](./plants/README.md) - Component package under `monster/plants` containing 15 files (`bane_bringer.lua`..`wilting_leaf_golem.lua`).
- [quests](./quests/README.md) - Intermediate blueprint grouping 43 subdirectories under `monster/quests`.
- [raids](./raids/README.md) - Component package under `monster/raids` containing 55 files (`arachir_the_ancient_one.lua`..`zulazza_the_corruptor.lua`).
- [reptiles](./reptiles/README.md) - Component package under `monster/reptiles` containing 42 files (`adult_goanna.lua`..`young_sea_serpent.lua`).
- [slimes](./slimes/README.md) - Component package under `monster/slimes` containing 12 files (`acid_blob.lua`..`squidgy_slime.lua`).
- [trainers](./trainers/README.md) - Component package under `monster/trainers` containing 1 files (`training_machine.lua`..`training_machine.lua`).
- [traps](./traps/README.md) - Component package under `monster/traps` containing 13 files (`deathslicer.lua`..`plaguethrower.lua`).
- [undeads](./undeads/README.md) - Component package under `monster/undeads` containing 63 files (`ahau.lua`..`zombie.lua`).
- [vermins](./vermins/README.md) - Component package under `monster/vermins` containing 62 files (`afflicted_strider.lua`..`wiggler.lua`).
- [wild_magics](./wild_magics/README.md) - Component package under `monster/wild_magics` containing 4 files (`wild_fire_magic.lua`..`wild_water_magic.lua`).

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [azure_frog.lua:monster.Bestiary]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [abyssal_calamary.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [agressive_chicken.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [alchemist_container.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [animated_snowman.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brittle_skeleton.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [askarak_demon.lua:monster.Bestiary]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dragolisk.lua:monster.Bestiary]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [candy_floss_elemental.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bones.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [breach_brood.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [druid_familiar.lua:monster.flags]

## Side Effects
- Registers monster type `Azure Frog` into the global `Game` engine registry via `mType:register(monster)` [azure_frog.lua:mType:register]
- Registers monster type `Abyssal Calamary` into the global `Game` engine registry via `mType:register(monster)` [abyssal_calamary.lua:mType:register]
- Registers monster type `Agressive Chicken` into the global `Game` engine registry via `mType:register(monster)` [agressive_chicken.lua:mType:register]
- Registers monster type `Alchemist Container` into the global `Game` engine registry via `mType:register(monster)` [alchemist_container.lua:mType:register]
- Registers monster type `Animated Snowman` into the global `Game` engine registry via `mType:register(monster)` [animated_snowman.lua:mType:register]
- Registers monster type `Brittle Skeleton` into the global `Game` engine registry via `mType:register(monster)` [brittle_skeleton.lua:mType:register]
- Registers monster type `Askarak Demon` into the global `Game` engine registry via `mType:register(monster)` [askarak_demon.lua:mType:register]
- Registers monster type `Dragolisk` into the global `Game` engine registry via `mType:register(monster)` [dragolisk.lua:mType:register]
- Registers monster type `Candy Floss Elemental` into the global `Game` engine registry via `mType:register(monster)` [candy_floss_elemental.lua:mType:register]
- Registers monster type `Bones` into the global `Game` engine registry via `mType:register(monster)` [bones.lua:mType:register]
- Registers monster type `Breach Brood` into the global `Game` engine registry via `mType:register(monster)` [breach_brood.lua:mType:register]
- Registers monster type `Druid familiar` into the global `Game` engine registry via `mType:register(monster)` [druid_familiar.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
