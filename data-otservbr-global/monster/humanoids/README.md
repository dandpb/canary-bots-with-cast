# Humanoids

## Overview
Component package under `monster/humanoids` containing 89 files (`broken_shaper.lua`..`young_troll.lua`).

## Interface
- Defines 89 script/configuration files (`broken_shaper.lua` through `young_troll.lua`) [broken_shaper.lua]
- `Game.createMonsterType("Broken Shaper")` and `mType:register(monster)` [broken_shaper.lua:Game.createMonsterType]
- `Game.createMonsterType("Bulltaur Alchemist")` and `mType:register(monster)` [bulltaur_alchemist.lua:Game.createMonsterType]
- `Game.createMonsterType("Bulltaur Brute")` and `mType:register(monster)` [bulltaur_brute.lua:Game.createMonsterType]
- `Game.createMonsterType("Bulltaur Forgepriest")` and `mType:register(monster)` [bulltaur_forgepriest.lua:Game.createMonsterType]
- `Game.createMonsterType("Chakoya Toolshaper")` and `mType:register(monster)` [chakoya_toolshaper.lua:Game.createMonsterType]
- `Game.createMonsterType("Chakoya Tribewarden")` and `mType:register(monster)` [chakoya_tribewarden.lua:Game.createMonsterType]
- `Game.createMonsterType("Chakoya Windcaller")` and `mType:register(monster)` [chakoya_windcaller.lua:Game.createMonsterType]
- `Game.createMonsterType("Cheese Thief")` and `mType:register(monster)` [cheese_thief.lua:Game.createMonsterType]
- `Game.createMonsterType("Corym Charlatan")` and `mType:register(monster)` [corym_charlatan.lua:Game.createMonsterType]
- `Game.createMonsterType("Corym Skirmisher")` and `mType:register(monster)` [corym_skirmisher.lua:Game.createMonsterType]
- `Game.createMonsterType("Corym Vanguard")` and `mType:register(monster)` [corym_vanguard.lua:Game.createMonsterType]
- `Game.createMonsterType("Crazed Summer Rearguard")` and `mType:register(monster)` [crazed_summer_rearguard.lua:Game.createMonsterType]
- `Game.createMonsterType("Crazed Summer Vanguard")` and `mType:register(monster)` [crazed_summer_vanguard.lua:Game.createMonsterType]
- `Game.createMonsterType("Crazed Winter Rearguard")` and `mType:register(monster)` [crazed_winter_rearguard.lua:Game.createMonsterType]
- `Game.createMonsterType("Crazed Winter Vanguard")` and `mType:register(monster)` [crazed_winter_vanguard.lua:Game.createMonsterType]
- `Game.createMonsterType("Dwarf")` and `mType:register(monster)` [dwarf.lua:Game.createMonsterType]
- `Game.createMonsterType("Dwarf Geomancer")` and `mType:register(monster)` [dwarf_geomancer.lua:Game.createMonsterType]
- `Game.createMonsterType("Dwarf Guard")` and `mType:register(monster)` [dwarf_guard.lua:Game.createMonsterType]
- `Game.createMonsterType("Dwarf Henchman")` and `mType:register(monster)` [dwarf_henchman.lua:Game.createMonsterType]
- `Game.createMonsterType("Dwarf Miner")` and `mType:register(monster)` [dwarf_miner.lua:Game.createMonsterType]
- `Game.createMonsterType("Dwarf Soldier")` and `mType:register(monster)` [dwarf_soldier.lua:Game.createMonsterType]
- `Game.createMonsterType("Dworc Fleshhunter")` and `mType:register(monster)` [dworc_fleshhunter.lua:Game.createMonsterType]
- `Game.createMonsterType("Dworc Venomsniper")` and `mType:register(monster)` [dworc_venomsniper.lua:Game.createMonsterType]
- `Game.createMonsterType("Dworc Voodoomaster")` and `mType:register(monster)` [dworc_voodoomaster.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [broken_shaper.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [broken_shaper.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bulltaur_alchemist.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bulltaur_alchemist.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bulltaur_brute.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bulltaur_brute.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bulltaur_forgepriest.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bulltaur_forgepriest.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [chakoya_toolshaper.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [chakoya_toolshaper.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [chakoya_tribewarden.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [chakoya_tribewarden.lua:monster.flags]

## Side Effects
- Registers monster type `Broken Shaper` into the global `Game` engine registry via `mType:register(monster)` [broken_shaper.lua:mType:register]
- Registers monster type `Bulltaur Alchemist` into the global `Game` engine registry via `mType:register(monster)` [bulltaur_alchemist.lua:mType:register]
- Registers monster type `Bulltaur Brute` into the global `Game` engine registry via `mType:register(monster)` [bulltaur_brute.lua:mType:register]
- Registers monster type `Bulltaur Forgepriest` into the global `Game` engine registry via `mType:register(monster)` [bulltaur_forgepriest.lua:mType:register]
- Registers monster type `Chakoya Toolshaper` into the global `Game` engine registry via `mType:register(monster)` [chakoya_toolshaper.lua:mType:register]
- Registers monster type `Chakoya Tribewarden` into the global `Game` engine registry via `mType:register(monster)` [chakoya_tribewarden.lua:mType:register]
- Registers monster type `Chakoya Windcaller` into the global `Game` engine registry via `mType:register(monster)` [chakoya_windcaller.lua:mType:register]
- Registers monster type `Cheese Thief` into the global `Game` engine registry via `mType:register(monster)` [cheese_thief.lua:mType:register]
- Registers monster type `Corym Charlatan` into the global `Game` engine registry via `mType:register(monster)` [corym_charlatan.lua:mType:register]
- Registers monster type `Corym Skirmisher` into the global `Game` engine registry via `mType:register(monster)` [corym_skirmisher.lua:mType:register]
- Registers monster type `Corym Vanguard` into the global `Game` engine registry via `mType:register(monster)` [corym_vanguard.lua:mType:register]
- Registers monster type `Crazed Summer Rearguard` into the global `Game` engine registry via `mType:register(monster)` [crazed_summer_rearguard.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
