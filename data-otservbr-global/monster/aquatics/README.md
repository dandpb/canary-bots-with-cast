# Aquatics

## Overview
Component package under `monster/aquatics` containing 40 files (`abyssal_calamary.lua`..`shark.lua`).

## Interface
- Defines 40 script/configuration files (`abyssal_calamary.lua` through `shark.lua`) [abyssal_calamary.lua]
- `Game.createMonsterType("Abyssal Calamary")` and `mType:register(monster)` [abyssal_calamary.lua:Game.createMonsterType]
- `Game.createMonsterType("Blood Crab")` and `mType:register(monster)` [blood_crab.lua:Game.createMonsterType]
- `Game.createMonsterType("Calamary")` and `mType:register(monster)` [calamary.lua:Game.createMonsterType]
- `Game.createMonsterType("Crab")` and `mType:register(monster)` [crab.lua:Game.createMonsterType]
- `Game.createMonsterType("Crustacea Gigantica")` and `mType:register(monster)` [crustacea_gigantica.lua:Game.createMonsterType]
- `Game.createMonsterType("Deathling Scout")` and `mType:register(monster)` [deathling_scout.lua:Game.createMonsterType]
- `Game.createMonsterType("Deathling Spellsinger")` and `mType:register(monster)` [deathling_spellsinger.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepling Brawler")` and `mType:register(monster)` [deepling_brawler.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepling Elite")` and `mType:register(monster)` [deepling_elite.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepling Guard")` and `mType:register(monster)` [deepling_guard.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepling Master Librarian")` and `mType:register(monster)` [deepling_master_librarian.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepling Scout")` and `mType:register(monster)` [deepling_scout.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepling Spellsinger")` and `mType:register(monster)` [deepling_spellsinger.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepling Tyrant")` and `mType:register(monster)` [deepling_tyrant.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepling Warrior")` and `mType:register(monster)` [deepling_warrior.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepling Worker")` and `mType:register(monster)` [deepling_worker.lua:Game.createMonsterType]
- `Game.createMonsterType("Deepsea Blood Crab")` and `mType:register(monster)` [deepsea_blood_crab.lua:Game.createMonsterType]
- `Game.createMonsterType("Fish")` and `mType:register(monster)` [fish.lua:Game.createMonsterType]
- `Game.createMonsterType("Jellyfish")` and `mType:register(monster)` [jellyfish.lua:Game.createMonsterType]
- `Game.createMonsterType("Manta Ray")` and `mType:register(monster)` [manta_ray.lua:Game.createMonsterType]
- `Game.createMonsterType("Northern Pike")` and `mType:register(monster)` [northern_pike.lua:Game.createMonsterType]
- `Game.createMonsterType("Quara Constrictor")` and `mType:register(monster)` [quara_constrictor.lua:Game.createMonsterType]
- `Game.createMonsterType("Quara Constrictor Scout")` and `mType:register(monster)` [quara_constrictor_scout.lua:Game.createMonsterType]
- `Game.createMonsterType("Quara Hydromancer")` and `mType:register(monster)` [quara_hydromancer.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [abyssal_calamary.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [abyssal_calamary.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [blood_crab.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [blood_crab.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [calamary.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [calamary.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [crab.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [crab.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [crustacea_gigantica.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [crustacea_gigantica.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [deathling_scout.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [deathling_scout.lua:monster.flags]

## Side Effects
- Registers monster type `Abyssal Calamary` into the global `Game` engine registry via `mType:register(monster)` [abyssal_calamary.lua:mType:register]
- Registers monster type `Blood Crab` into the global `Game` engine registry via `mType:register(monster)` [blood_crab.lua:mType:register]
- Registers monster type `Calamary` into the global `Game` engine registry via `mType:register(monster)` [calamary.lua:mType:register]
- Registers monster type `Crab` into the global `Game` engine registry via `mType:register(monster)` [crab.lua:mType:register]
- Registers monster type `Crustacea Gigantica` into the global `Game` engine registry via `mType:register(monster)` [crustacea_gigantica.lua:mType:register]
- Registers monster type `Deathling Scout` into the global `Game` engine registry via `mType:register(monster)` [deathling_scout.lua:mType:register]
- Registers monster type `Deathling Spellsinger` into the global `Game` engine registry via `mType:register(monster)` [deathling_spellsinger.lua:mType:register]
- Registers monster type `Deepling Brawler` into the global `Game` engine registry via `mType:register(monster)` [deepling_brawler.lua:mType:register]
- Registers monster type `Deepling Elite` into the global `Game` engine registry via `mType:register(monster)` [deepling_elite.lua:mType:register]
- Registers monster type `Deepling Guard` into the global `Game` engine registry via `mType:register(monster)` [deepling_guard.lua:mType:register]
- Registers monster type `Deepling Master Librarian` into the global `Game` engine registry via `mType:register(monster)` [deepling_master_librarian.lua:mType:register]
- Registers monster type `Deepling Scout` into the global `Game` engine registry via `mType:register(monster)` [deepling_scout.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
