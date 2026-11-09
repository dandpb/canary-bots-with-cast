# Giants

## Overview
Component package under `monster/giants` containing 16 files (`beast_hulking_prehemoth.lua`..`orclops_ravager.lua`).

## Interface
- `Game.createMonsterType("Beast Hulking Prehemoth")` and `mType:register(monster)` [beast_hulking_prehemoth.lua:Game.createMonsterType]
- `Game.createMonsterType("Behemoth")` and `mType:register(monster)` [behemoth.lua:Game.createMonsterType]
- `Game.createMonsterType("Cyclops")` and `mType:register(monster)` [cyclops.lua:Game.createMonsterType]
- `Game.createMonsterType("Cyclops Drone")` and `mType:register(monster)` [cyclops_drone.lua:Game.createMonsterType]
- `Game.createMonsterType("Cyclops Smith")` and `mType:register(monster)` [cyclops_smith.lua:Game.createMonsterType]
- `Game.createMonsterType("Frost Giant")` and `mType:register(monster)` [frost_giant.lua:Game.createMonsterType]
- `Game.createMonsterType("Frost Giantess")` and `mType:register(monster)` [frost_giantess.lua:Game.createMonsterType]
- `Game.createMonsterType("Hulking Prehemoth")` and `mType:register(monster)` [hulking_prehemoth.lua:Game.createMonsterType]
- `Game.createMonsterType("Ogre Brute")` and `mType:register(monster)` [ogre_brute.lua:Game.createMonsterType]
- `Game.createMonsterType("Ogre Rowdy")` and `mType:register(monster)` [ogre_rowdy.lua:Game.createMonsterType]
- `Game.createMonsterType("Ogre Ruffian")` and `mType:register(monster)` [ogre_ruffian.lua:Game.createMonsterType]
- `Game.createMonsterType("Ogre Sage")` and `mType:register(monster)` [ogre_sage.lua:Game.createMonsterType]
- `Game.createMonsterType("Ogre Savage")` and `mType:register(monster)` [ogre_savage.lua:Game.createMonsterType]
- `Game.createMonsterType("Ogre Shaman")` and `mType:register(monster)` [ogre_shaman.lua:Game.createMonsterType]
- `Game.createMonsterType("Orclops Doomhauler")` and `mType:register(monster)` [orclops_doomhauler.lua:Game.createMonsterType]
- `Game.createMonsterType("Orclops Ravager")` and `mType:register(monster)` [orclops_ravager.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [beast_hulking_prehemoth.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [behemoth.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [behemoth.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [cyclops.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cyclops.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [cyclops_drone.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cyclops_drone.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [cyclops_smith.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cyclops_smith.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [frost_giant.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [frost_giant.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [frost_giantess.lua:monster.Bestiary]

## Side Effects
- Registers monster type `Beast Hulking Prehemoth` into the global `Game` engine registry via `mType:register(monster)` [beast_hulking_prehemoth.lua:mType:register]
- Registers monster type `Behemoth` into the global `Game` engine registry via `mType:register(monster)` [behemoth.lua:mType:register]
- Registers monster type `Cyclops` into the global `Game` engine registry via `mType:register(monster)` [cyclops.lua:mType:register]
- Registers monster type `Cyclops Drone` into the global `Game` engine registry via `mType:register(monster)` [cyclops_drone.lua:mType:register]
- Registers monster type `Cyclops Smith` into the global `Game` engine registry via `mType:register(monster)` [cyclops_smith.lua:mType:register]
- Registers monster type `Frost Giant` into the global `Game` engine registry via `mType:register(monster)` [frost_giant.lua:mType:register]
- Registers monster type `Frost Giantess` into the global `Game` engine registry via `mType:register(monster)` [frost_giantess.lua:mType:register]
- Registers monster type `Hulking Prehemoth` into the global `Game` engine registry via `mType:register(monster)` [hulking_prehemoth.lua:mType:register]
- Registers monster type `Ogre Brute` into the global `Game` engine registry via `mType:register(monster)` [ogre_brute.lua:mType:register]
- Registers monster type `Ogre Rowdy` into the global `Game` engine registry via `mType:register(monster)` [ogre_rowdy.lua:mType:register]
- Registers monster type `Ogre Ruffian` into the global `Game` engine registry via `mType:register(monster)` [ogre_ruffian.lua:mType:register]
- Registers monster type `Ogre Sage` into the global `Game` engine registry via `mType:register(monster)` [ogre_sage.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
