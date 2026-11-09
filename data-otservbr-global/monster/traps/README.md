# Traps

## Overview
Component package under `monster/traps` containing 13 files (`deathslicer.lua`..`plaguethrower.lua`).

## Interface
- `Game.createMonsterType("Deathslicer")` and `mType:register(monster)` [deathslicer.lua:Game.createMonsterType]
- `Game.createMonsterType("Deaththrower")` and `mType:register(monster)` [deaththrower.lua:Game.createMonsterType]
- `Game.createMonsterType("Demon Summoner")` and `mType:register(monster)` [demon_summoner.lua:Game.createMonsterType]
- `Game.createMonsterType("Floor Blob")` and `mType:register(monster)` [floor_blob.lua:Game.createMonsterType]
- `Game.createMonsterType("Hell Hole")` and `mType:register(monster)` [hell_hole.lua:Game.createMonsterType]
- `Game.createMonsterType("Hive Pore")` and `mType:register(monster)` [hive_pore.lua:Game.createMonsterType]
- `Game.createMonsterType("Lavahole")` and `mType:register(monster)` [lavahole.lua:Game.createMonsterType]
- `Game.createMonsterType("Magic Pillar")` and `mType:register(monster)` [magic_pillar.lua:Game.createMonsterType]
- `Game.createMonsterType("Magicthrower")` and `mType:register(monster)` [magicthrower.lua:Game.createMonsterType]
- `Game.createMonsterType("Mechanical Fighter")` and `mType:register(monster)` [mechanical_fighter.lua:Game.createMonsterType]
- `Game.createMonsterType("Mimic")` and `mType:register(monster)` [mimic.lua:Game.createMonsterType]
- `Game.createMonsterType("Pillar")` and `mType:register(monster)` [pillar.lua:Game.createMonsterType]
- `Game.createMonsterType("Plaguethrower")` and `mType:register(monster)` [plaguethrower.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [deathslicer.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [deaththrower.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [demon_summoner.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [floor_blob.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [hell_hole.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [hive_pore.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lavahole.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [magic_pillar.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [magicthrower.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mechanical_fighter.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mimic.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [pillar.lua:monster.flags]

## Side Effects
- Registers monster type `Deathslicer` into the global `Game` engine registry via `mType:register(monster)` [deathslicer.lua:mType:register]
- Registers monster type `Deaththrower` into the global `Game` engine registry via `mType:register(monster)` [deaththrower.lua:mType:register]
- Registers monster type `Demon Summoner` into the global `Game` engine registry via `mType:register(monster)` [demon_summoner.lua:mType:register]
- Registers monster type `Floor Blob` into the global `Game` engine registry via `mType:register(monster)` [floor_blob.lua:mType:register]
- Registers monster type `Hell Hole` into the global `Game` engine registry via `mType:register(monster)` [hell_hole.lua:mType:register]
- Registers monster type `Hive Pore` into the global `Game` engine registry via `mType:register(monster)` [hive_pore.lua:mType:register]
- Registers monster type `Lavahole` into the global `Game` engine registry via `mType:register(monster)` [lavahole.lua:mType:register]
- Registers monster type `Magic Pillar` into the global `Game` engine registry via `mType:register(monster)` [magic_pillar.lua:mType:register]
- Registers monster type `Magicthrower` into the global `Game` engine registry via `mType:register(monster)` [magicthrower.lua:mType:register]
- Registers monster type `Mechanical Fighter` into the global `Game` engine registry via `mType:register(monster)` [mechanical_fighter.lua:mType:register]
- Registers monster type `Mimic` into the global `Game` engine registry via `mType:register(monster)` [mimic.lua:mType:register]
- Registers monster type `Pillar` into the global `Game` engine registry via `mType:register(monster)` [pillar.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
