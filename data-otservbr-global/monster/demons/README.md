# Demons

## Overview
Component package under `monster/demons` containing 39 files (`askarak_demon.lua`..`vexclaw.lua`).

## Interface
- Defines 39 script/configuration files (`askarak_demon.lua` through `vexclaw.lua`) [askarak_demon.lua]
- `Game.createMonsterType("Askarak Demon")` and `mType:register(monster)` [askarak_demon.lua:Game.createMonsterType]
- `Game.createMonsterType("Askarak Lord")` and `mType:register(monster)` [askarak_lord.lua:Game.createMonsterType]
- `Game.createMonsterType("Askarak Prince")` and `mType:register(monster)` [askarak_prince.lua:Game.createMonsterType]
- `Game.createMonsterType("Brinebrute Inferniarch")` and `mType:register(monster)` [brinebrute_inferniarch.lua:Game.createMonsterType]
- `Game.createMonsterType("Broodrider Inferniarch")` and `mType:register(monster)` [broodrider_inferniarch.lua:Game.createMonsterType]
- `Game.createMonsterType("Dark Torturer")` and `mType:register(monster)` [dark_torturer.lua:Game.createMonsterType]
- `Game.createMonsterType("Dawnfire Asura")` and `mType:register(monster)` [dawnfire_asura.lua:Game.createMonsterType]
- `Game.createMonsterType("Demon")` and `mType:register(monster)` [demon.lua:Game.createMonsterType]
- `Game.createMonsterType("Demon Outcast")` and `mType:register(monster)` [demon_outcast.lua:Game.createMonsterType]
- `Game.createMonsterType("Destroyer")` and `mType:register(monster)` [destroyer.lua:Game.createMonsterType]
- `Game.createMonsterType("Diabolic Imp")` and `mType:register(monster)` [diabolic_imp.lua:Game.createMonsterType]
- `Game.createMonsterType("Duskbringer")` and `mType:register(monster)` [duskbringer.lua:Game.createMonsterType]
- `Game.createMonsterType("Fire Devil")` and `mType:register(monster)` [fire_devil.lua:Game.createMonsterType]
- `Game.createMonsterType("Floating Savant")` and `mType:register(monster)` [floating_savant.lua:Game.createMonsterType]
- `Game.createMonsterType("Frost Flower Asura")` and `mType:register(monster)` [frost_flower_asura.lua:Game.createMonsterType]
- `Game.createMonsterType("Fury")` and `mType:register(monster)` [fury.lua:Game.createMonsterType]
- `Game.createMonsterType("Gorger Inferniarch")` and `mType:register(monster)` [gorger_inferniarch.lua:Game.createMonsterType]
- `Game.createMonsterType("Gozzler")` and `mType:register(monster)` [gozzler.lua:Game.createMonsterType]
- `Game.createMonsterType("Grimeleech")` and `mType:register(monster)` [grimeleech.lua:Game.createMonsterType]
- `Game.createMonsterType("Hellfire Fighter")` and `mType:register(monster)` [hellfire_fighter.lua:Game.createMonsterType]
- `Game.createMonsterType("Hellflayer")` and `mType:register(monster)` [hellflayer.lua:Game.createMonsterType]
- `Game.createMonsterType("Hellhound")` and `mType:register(monster)` [hellhound.lua:Game.createMonsterType]
- `Game.createMonsterType("Hellhunter Inferniarch")` and `mType:register(monster)` [hellhunter_inferniarch.lua:Game.createMonsterType]
- `Game.createMonsterType("Hellspawn")` and `mType:register(monster)` [hellspawn.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [askarak_demon.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [askarak_demon.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [askarak_lord.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [askarak_lord.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [askarak_prince.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [askarak_prince.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [brinebrute_inferniarch.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brinebrute_inferniarch.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [broodrider_inferniarch.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [broodrider_inferniarch.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dark_torturer.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dark_torturer.lua:monster.flags]

## Side Effects
- Registers monster type `Askarak Demon` into the global `Game` engine registry via `mType:register(monster)` [askarak_demon.lua:mType:register]
- Registers monster type `Askarak Lord` into the global `Game` engine registry via `mType:register(monster)` [askarak_lord.lua:mType:register]
- Registers monster type `Askarak Prince` into the global `Game` engine registry via `mType:register(monster)` [askarak_prince.lua:mType:register]
- Registers monster type `Brinebrute Inferniarch` into the global `Game` engine registry via `mType:register(monster)` [brinebrute_inferniarch.lua:mType:register]
- Registers monster type `Broodrider Inferniarch` into the global `Game` engine registry via `mType:register(monster)` [broodrider_inferniarch.lua:mType:register]
- Registers monster type `Dark Torturer` into the global `Game` engine registry via `mType:register(monster)` [dark_torturer.lua:mType:register]
- Registers monster type `Dawnfire Asura` into the global `Game` engine registry via `mType:register(monster)` [dawnfire_asura.lua:mType:register]
- Registers monster type `Demon` into the global `Game` engine registry via `mType:register(monster)` [demon.lua:mType:register]
- Registers monster type `Demon Outcast` into the global `Game` engine registry via `mType:register(monster)` [demon_outcast.lua:mType:register]
- Registers monster type `Destroyer` into the global `Game` engine registry via `mType:register(monster)` [destroyer.lua:mType:register]
- Registers monster type `Diabolic Imp` into the global `Game` engine registry via `mType:register(monster)` [diabolic_imp.lua:mType:register]
- Registers monster type `Duskbringer` into the global `Game` engine registry via `mType:register(monster)` [duskbringer.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
