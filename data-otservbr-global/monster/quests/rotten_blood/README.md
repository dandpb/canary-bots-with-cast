# Rotten Blood

## Overview
Component package under `monster/quests/rotten_blood` containing 22 files (`bloated_man-maggot.lua`..`wandering_pillar.lua`).

## Interface
- `Game.createMonsterType("Bloated Man-Maggot")` and `mType:register(monster)` [bloated_man-maggot.lua:Game.createMonsterType]
- `Game.createMonsterType("Converter")` and `mType:register(monster)` [converter.lua:Game.createMonsterType]
- `Game.createMonsterType("Darklight Construct")` and `mType:register(monster)` [darklight_construct.lua:Game.createMonsterType]
- `Game.createMonsterType("Darklight Emitter")` and `mType:register(monster)` [darklight_emitter.lua:Game.createMonsterType]
- `Game.createMonsterType("Darklight Matter")` and `mType:register(monster)` [darklight_matter.lua:Game.createMonsterType]
- `Game.createMonsterType("Darklight Source")` and `mType:register(monster)` [darklight_source.lua:Game.createMonsterType]
- `Game.createMonsterType("Darklight Striker")` and `mType:register(monster)` [darklight_striker.lua:Game.createMonsterType]
- `Game.createMonsterType("Echo Of Chagorz")` and `mType:register(monster)` [echo_of_chagorz.lua:Game.createMonsterType]
- `Game.createMonsterType("Echo Of Ichgahal")` and `mType:register(monster)` [echo_of_ichgahal.lua:Game.createMonsterType]
- `Game.createMonsterType("Echo Of Murcion")` and `mType:register(monster)` [echo_of_murcion.lua:Game.createMonsterType]
- `Game.createMonsterType("Echo Of Vemiath")` and `mType:register(monster)` [echo_of_vemiath.lua:Game.createMonsterType]
- `Game.createMonsterType("Elder Bloodjaw")` and `mType:register(monster)` [elder_bloodjaw.lua:Game.createMonsterType]
- `Game.createMonsterType("Meandering Mushroom")` and `mType:register(monster)` [meandering_mushroom.lua:Game.createMonsterType]
- `Game.createMonsterType("Mushroom")` and `mType:register(monster)` [mushroom.lua:Game.createMonsterType]
- `Game.createMonsterType("Mycobiontic Beetle")` and `mType:register(monster)` [mycobiontic_beetle.lua:Game.createMonsterType]
- `Game.createMonsterType("Oozing Carcass")` and `mType:register(monster)` [oozing_carcass.lua:Game.createMonsterType]
- `Game.createMonsterType("Oozing Corpus")` and `mType:register(monster)` [oozing_corpus.lua:Game.createMonsterType]
- `Game.createMonsterType("Rotten Man-Maggot")` and `mType:register(monster)` [rotten_man-maggot.lua:Game.createMonsterType]
- `Game.createMonsterType("Sopping Carcass")` and `mType:register(monster)` [sopping_carcass.lua:Game.createMonsterType]
- `Game.createMonsterType("Sopping Corpus")` and `mType:register(monster)` [sopping_corpus.lua:Game.createMonsterType]
- `Game.createMonsterType("Walking Pillar")` and `mType:register(monster)` [walking_pillar.lua:Game.createMonsterType]
- `Game.createMonsterType("Wandering Pillar")` and `mType:register(monster)` [wandering_pillar.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bloated_man-maggot.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bloated_man-maggot.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [converter.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [converter.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [darklight_construct.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [darklight_construct.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [darklight_emitter.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [darklight_emitter.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [darklight_matter.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [darklight_matter.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [darklight_source.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [darklight_source.lua:monster.flags]

## Side Effects
- Registers monster type `Bloated Man-Maggot` into the global `Game` engine registry via `mType:register(monster)` [bloated_man-maggot.lua:mType:register]
- Registers monster type `Converter` into the global `Game` engine registry via `mType:register(monster)` [converter.lua:mType:register]
- Registers monster type `Darklight Construct` into the global `Game` engine registry via `mType:register(monster)` [darklight_construct.lua:mType:register]
- Registers monster type `Darklight Emitter` into the global `Game` engine registry via `mType:register(monster)` [darklight_emitter.lua:mType:register]
- Registers monster type `Darklight Matter` into the global `Game` engine registry via `mType:register(monster)` [darklight_matter.lua:mType:register]
- Registers monster type `Darklight Source` into the global `Game` engine registry via `mType:register(monster)` [darklight_source.lua:mType:register]
- Registers monster type `Darklight Striker` into the global `Game` engine registry via `mType:register(monster)` [darklight_striker.lua:mType:register]
- Registers monster type `Echo Of Chagorz` into the global `Game` engine registry via `mType:register(monster)` [echo_of_chagorz.lua:mType:register]
- Registers monster type `Echo Of Ichgahal` into the global `Game` engine registry via `mType:register(monster)` [echo_of_ichgahal.lua:mType:register]
- Registers monster type `Echo Of Murcion` into the global `Game` engine registry via `mType:register(monster)` [echo_of_murcion.lua:mType:register]
- Registers monster type `Echo Of Vemiath` into the global `Game` engine registry via `mType:register(monster)` [echo_of_vemiath.lua:mType:register]
- Registers monster type `Elder Bloodjaw` into the global `Game` engine registry via `mType:register(monster)` [elder_bloodjaw.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
