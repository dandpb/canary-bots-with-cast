# Amphibics

## Overview
Component package under `monster/amphibics` containing 12 files (`azure_frog.lua`..`toad.lua`).

## Interface
- `Game.createMonsterType("Azure Frog")` and `mType:register(monster)` [azure_frog.lua:Game.createMonsterType]
- `Game.createMonsterType("Bog Frog")` and `mType:register(monster)` [bog_frog.lua:Game.createMonsterType]
- `Game.createMonsterType("Coral Frog")` and `mType:register(monster)` [coral_frog.lua:Game.createMonsterType]
- `Game.createMonsterType("Crimson Frog")` and `mType:register(monster)` [crimson_frog.lua:Game.createMonsterType]
- `Game.createMonsterType("Deathspawn")` and `mType:register(monster)` [deathspawn.lua:Game.createMonsterType]
- `Game.createMonsterType("Filth Toad")` and `mType:register(monster)` [filth_toad.lua:Game.createMonsterType]
- `Game.createMonsterType("Green Frog")` and `mType:register(monster)` [green_frog.lua:Game.createMonsterType]
- `Game.createMonsterType("Infernal Frog")` and `mType:register(monster)` [infernal_frog.lua:Game.createMonsterType]
- `Game.createMonsterType("Makara")` and `mType:register(monster)` [makara.lua:Game.createMonsterType]
- `Game.createMonsterType("Orchid Frog")` and `mType:register(monster)` [orchid_frog.lua:Game.createMonsterType]
- `Game.createMonsterType("Salamander")` and `mType:register(monster)` [salamander.lua:Game.createMonsterType]
- `Game.createMonsterType("Toad")` and `mType:register(monster)` [toad.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [azure_frog.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [azure_frog.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bog_frog.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bog_frog.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [coral_frog.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [coral_frog.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [crimson_frog.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [crimson_frog.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [deathspawn.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [filth_toad.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [filth_toad.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [green_frog.lua:monster.Bestiary]

## Side Effects
- Registers monster type `Azure Frog` into the global `Game` engine registry via `mType:register(monster)` [azure_frog.lua:mType:register]
- Registers monster type `Bog Frog` into the global `Game` engine registry via `mType:register(monster)` [bog_frog.lua:mType:register]
- Registers monster type `Coral Frog` into the global `Game` engine registry via `mType:register(monster)` [coral_frog.lua:mType:register]
- Registers monster type `Crimson Frog` into the global `Game` engine registry via `mType:register(monster)` [crimson_frog.lua:mType:register]
- Registers monster type `Deathspawn` into the global `Game` engine registry via `mType:register(monster)` [deathspawn.lua:mType:register]
- Registers monster type `Filth Toad` into the global `Game` engine registry via `mType:register(monster)` [filth_toad.lua:mType:register]
- Registers monster type `Green Frog` into the global `Game` engine registry via `mType:register(monster)` [green_frog.lua:mType:register]
- Registers monster type `Infernal Frog` into the global `Game` engine registry via `mType:register(monster)` [infernal_frog.lua:mType:register]
- Registers monster type `Makara` into the global `Game` engine registry via `mType:register(monster)` [makara.lua:mType:register]
- Registers monster type `Orchid Frog` into the global `Game` engine registry via `mType:register(monster)` [orchid_frog.lua:mType:register]
- Registers monster type `Salamander` into the global `Game` engine registry via `mType:register(monster)` [salamander.lua:mType:register]
- Registers monster type `Toad` into the global `Game` engine registry via `mType:register(monster)` [toad.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
