# Dragons

## Overview
Component package under `monster/dragons` containing 17 files (`dragolisk.lua`..`wyrm.lua`).

## Interface
- `Game.createMonsterType("Dragolisk")` and `mType:register(monster)` [dragolisk.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragon")` and `mType:register(monster)` [dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragon Hatchling")` and `mType:register(monster)` [dragon_hatchling.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragon Lord")` and `mType:register(monster)` [dragon_lord.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragon Lord Hatchling")` and `mType:register(monster)` [dragon_lord_hatchling.lua:Game.createMonsterType]
- `Game.createMonsterType("Draken Abomination")` and `mType:register(monster)` [draken_abomination.lua:Game.createMonsterType]
- `Game.createMonsterType("Draken Elite")` and `mType:register(monster)` [draken_elite.lua:Game.createMonsterType]
- `Game.createMonsterType("Draken Spellweaver")` and `mType:register(monster)` [draken_spellweaver.lua:Game.createMonsterType]
- `Game.createMonsterType("Draken Warmaster")` and `mType:register(monster)` [draken_warmaster.lua:Game.createMonsterType]
- `Game.createMonsterType("Elder Wyrm")` and `mType:register(monster)` [elder_wyrm.lua:Game.createMonsterType]
- `Game.createMonsterType("Frost Dragon")` and `mType:register(monster)` [frost_dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Frost Dragon Hatchling")` and `mType:register(monster)` [frost_dragon_hatchling.lua:Game.createMonsterType]
- `Game.createMonsterType("Ghastly Dragon")` and `mType:register(monster)` [ghastly_dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Hydra")` and `mType:register(monster)` [hydra.lua:Game.createMonsterType]
- `Game.createMonsterType("Mega Dragon")` and `mType:register(monster)` [mega_dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Wardragon")` and `mType:register(monster)` [war_dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Wyrm")` and `mType:register(monster)` [wyrm.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dragolisk.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragolisk.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dragon.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragon.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dragon_hatchling.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragon_hatchling.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dragon_lord.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragon_lord.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dragon_lord_hatchling.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragon_lord_hatchling.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [draken_abomination.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [draken_abomination.lua:monster.flags]

## Side Effects
- Registers monster type `Dragolisk` into the global `Game` engine registry via `mType:register(monster)` [dragolisk.lua:mType:register]
- Registers monster type `Dragon` into the global `Game` engine registry via `mType:register(monster)` [dragon.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [dragon.lua:monster.events]
- Registers monster type `Dragon Hatchling` into the global `Game` engine registry via `mType:register(monster)` [dragon_hatchling.lua:mType:register]
- Registers monster type `Dragon Lord` into the global `Game` engine registry via `mType:register(monster)` [dragon_lord.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [dragon_lord.lua:monster.events]
- Registers monster type `Dragon Lord Hatchling` into the global `Game` engine registry via `mType:register(monster)` [dragon_lord_hatchling.lua:mType:register]
- Registers monster type `Draken Abomination` into the global `Game` engine registry via `mType:register(monster)` [draken_abomination.lua:mType:register]
- Registers monster type `Draken Elite` into the global `Game` engine registry via `mType:register(monster)` [draken_elite.lua:mType:register]
- Registers monster type `Draken Spellweaver` into the global `Game` engine registry via `mType:register(monster)` [draken_spellweaver.lua:mType:register]
- Registers monster type `Draken Warmaster` into the global `Game` engine registry via `mType:register(monster)` [draken_warmaster.lua:mType:register]
- Registers monster type `Elder Wyrm` into the global `Game` engine registry via `mType:register(monster)` [elder_wyrm.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
