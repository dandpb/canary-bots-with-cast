# Slimes

## Overview
Component package under `monster/slimes` containing 12 files (`acid_blob.lua`..`squidgy_slime.lua`).

## Interface
- `Game.createMonsterType("Acid Blob")` and `mType:register(monster)` [acid_blob.lua:Game.createMonsterType]
- `Game.createMonsterType("Chocolate Blob")` and `mType:register(monster)` [chocolate_blob.lua:Game.createMonsterType]
- `Game.createMonsterType("Death Blob")` and `mType:register(monster)` [death_blob.lua:Game.createMonsterType]
- `Game.createMonsterType("Defiler")` and `mType:register(monster)` [defiler.lua:Game.createMonsterType]
- `Game.createMonsterType("Devourer")` and `mType:register(monster)` [devourer.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth Blob")` and `mType:register(monster)` [glooth_blob.lua:Game.createMonsterType]
- `Game.createMonsterType("Ink Blob")` and `mType:register(monster)` [ink_blob.lua:Game.createMonsterType]
- `Game.createMonsterType("Mercury Blob")` and `mType:register(monster)` [mercury_blob.lua:Game.createMonsterType]
- `Game.createMonsterType("Midnight Spawn")` and `mType:register(monster)` [midnight_spawn.lua:Game.createMonsterType]
- `Game.createMonsterType("Slime")` and `mType:register(monster)` [slime.lua:Game.createMonsterType]
- `Game.createMonsterType("Son of Verminor")` and `mType:register(monster)` [son_of_verminor.lua:Game.createMonsterType]
- `Game.createMonsterType("Squidgy Slime")` and `mType:register(monster)` [squidgy_slime.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [acid_blob.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [acid_blob.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [chocolate_blob.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [chocolate_blob.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [death_blob.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [death_blob.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [defiler.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [defiler.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [devourer.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [devourer.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [glooth_blob.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [glooth_blob.lua:monster.flags]

## Side Effects
- Registers monster type `Acid Blob` into the global `Game` engine registry via `mType:register(monster)` [acid_blob.lua:mType:register]
- Registers monster type `Chocolate Blob` into the global `Game` engine registry via `mType:register(monster)` [chocolate_blob.lua:mType:register]
- Registers monster type `Death Blob` into the global `Game` engine registry via `mType:register(monster)` [death_blob.lua:mType:register]
- Registers monster type `Defiler` into the global `Game` engine registry via `mType:register(monster)` [defiler.lua:mType:register]
- Registers monster type `Devourer` into the global `Game` engine registry via `mType:register(monster)` [devourer.lua:mType:register]
- Registers monster type `Glooth Blob` into the global `Game` engine registry via `mType:register(monster)` [glooth_blob.lua:mType:register]
- Registers monster type `Ink Blob` into the global `Game` engine registry via `mType:register(monster)` [ink_blob.lua:mType:register]
- Registers monster type `Mercury Blob` into the global `Game` engine registry via `mType:register(monster)` [mercury_blob.lua:mType:register]
- Registers monster type `Midnight Spawn` into the global `Game` engine registry via `mType:register(monster)` [midnight_spawn.lua:mType:register]
- Registers monster type `Slime` into the global `Game` engine registry via `mType:register(monster)` [slime.lua:mType:register]
- Registers monster type `Son of Verminor` into the global `Game` engine registry via `mType:register(monster)` [son_of_verminor.lua:mType:register]
- Registers monster type `Squidgy Slime` into the global `Game` engine registry via `mType:register(monster)` [squidgy_slime.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
