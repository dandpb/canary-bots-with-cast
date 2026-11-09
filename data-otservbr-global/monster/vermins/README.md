# Vermins

## Overview
Component package under `monster/vermins` containing 62 files (`afflicted_strider.lua`..`wiggler.lua`).

## Interface
- Defines 62 script/configuration files (`afflicted_strider.lua` through `wiggler.lua`) [afflicted_strider.lua]
- `Game.createMonsterType("Afflicted Strider")` and `mType:register(monster)` [afflicted_strider.lua:Game.createMonsterType]
- `Game.createMonsterType("Ancient Scarab")` and `mType:register(monster)` [ancient_scarab.lua:Game.createMonsterType]
- `Game.createMonsterType("Blemished Spawn")` and `mType:register(monster)` [blemished_spawn.lua:Game.createMonsterType]
- `Game.createMonsterType("Brimstone Bug")` and `mType:register(monster)` [brimstone_bug.lua:Game.createMonsterType]
- `Game.createMonsterType("Bug")` and `mType:register(monster)` [bug.lua:Game.createMonsterType]
- `Game.createMonsterType("Burrowing Beetle")` and `mType:register(monster)` [burrowing_beetle.lua:Game.createMonsterType]
- `Game.createMonsterType("Butterfly")` and `mType:register(monster)` [butterfly.lua:Game.createMonsterType]
- `Game.createMonsterType("Carrion Worm")` and `mType:register(monster)` [carrion_worm.lua:Game.createMonsterType]
- `Game.createMonsterType("Cave Chimera")` and `mType:register(monster)` [cave_chimera.lua:Game.createMonsterType]
- `Game.createMonsterType("Cave Devourer")` and `mType:register(monster)` [cave_devourer.lua:Game.createMonsterType]
- `Game.createMonsterType("Centipede")` and `mType:register(monster)` [centipede.lua:Game.createMonsterType]
- `Game.createMonsterType("Chasm Spawn")` and `mType:register(monster)` [chasm_spawn.lua:Game.createMonsterType]
- `Game.createMonsterType("Cockroach")` and `mType:register(monster)` [cockroach.lua:Game.createMonsterType]
- `Game.createMonsterType("Crawler")` and `mType:register(monster)` [crawler.lua:Game.createMonsterType]
- `Game.createMonsterType("Crystal Spider")` and `mType:register(monster)` [crystal_spider.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepworm")` and `mType:register(monster)` [deepworm.lua:Game.createMonsterType]
- `Game.createMonsterType("Diremaw")` and `mType:register(monster)` [diremaw.lua:Game.createMonsterType]
- `Game.createMonsterType("Drillworm")` and `mType:register(monster)` [drillworm.lua:Game.createMonsterType]
- `Game.createMonsterType("Emerald Damselfly")` and `mType:register(monster)` [emerald_damselfly.lua:Game.createMonsterType]
- `Game.createMonsterType("Enpa Yolo")` and `mType:register(monster)` [enpa_yolo.lua:Game.createMonsterType]
- `Game.createMonsterType("Exotic Cave Spider")` and `mType:register(monster)` [exotic_cave_spider.lua:Game.createMonsterType]
- `Game.createMonsterType("Eyeless Devourer")` and `mType:register(monster)` [eyeless_devourer.lua:Game.createMonsterType]
- `Game.createMonsterType("Giant Spider")` and `mType:register(monster)` [giant_spider.lua:Game.createMonsterType]
- `Game.createMonsterType("Hibernal Moth")` and `mType:register(monster)` [hibernal_moth.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [afflicted_strider.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [afflicted_strider.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [ancient_scarab.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ancient_scarab.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [blemished_spawn.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [blemished_spawn.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [brimstone_bug.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brimstone_bug.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bug.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bug.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [burrowing_beetle.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [butterfly.lua:monster.Bestiary]

## Side Effects
- Registers monster type `Afflicted Strider` into the global `Game` engine registry via `mType:register(monster)` [afflicted_strider.lua:mType:register]
- Registers monster type `Ancient Scarab` into the global `Game` engine registry via `mType:register(monster)` [ancient_scarab.lua:mType:register]
- Registers monster type `Blemished Spawn` into the global `Game` engine registry via `mType:register(monster)` [blemished_spawn.lua:mType:register]
- Registers monster type `Brimstone Bug` into the global `Game` engine registry via `mType:register(monster)` [brimstone_bug.lua:mType:register]
- Registers monster type `Bug` into the global `Game` engine registry via `mType:register(monster)` [bug.lua:mType:register]
- Registers monster type `Burrowing Beetle` into the global `Game` engine registry via `mType:register(monster)` [burrowing_beetle.lua:mType:register]
- Registers monster type `Butterfly` into the global `Game` engine registry via `mType:register(monster)` [butterfly.lua:mType:register]
- Registers monster type `Carrion Worm` into the global `Game` engine registry via `mType:register(monster)` [carrion_worm.lua:mType:register]
- Registers monster type `Cave Chimera` into the global `Game` engine registry via `mType:register(monster)` [cave_chimera.lua:mType:register]
- Registers monster type `Cave Devourer` into the global `Game` engine registry via `mType:register(monster)` [cave_devourer.lua:mType:register]
- Registers monster type `Centipede` into the global `Game` engine registry via `mType:register(monster)` [centipede.lua:mType:register]
- Registers monster type `Chasm Spawn` into the global `Game` engine registry via `mType:register(monster)` [chasm_spawn.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
