# Plants

## Overview
Component package under `monster/plants` containing 15 files (`bane_bringer.lua`..`wilting_leaf_golem.lua`).

## Interface
- `Game.createMonsterType("Bane Bringer")` and `mType:register(monster)` [bane_bringer.lua:Game.createMonsterType]
- `Game.createMonsterType("Carniphila")` and `mType:register(monster)` [carniphila.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth Anemone")` and `mType:register(monster)` [glooth_anemone.lua:Game.createMonsterType]
- `Game.createMonsterType("Haunted Treeling")` and `mType:register(monster)` [haunted_treeling.lua:Game.createMonsterType]
- `Game.createMonsterType("Hideous Fungus")` and `mType:register(monster)` [hideous_fungus.lua:Game.createMonsterType]
- `Game.createMonsterType("Humongous Fungus")` and `mType:register(monster)` [humongous_fungus.lua:Game.createMonsterType]
- `Game.createMonsterType("Leaf Golem")` and `mType:register(monster)` [leaf_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Omnivora")` and `mType:register(monster)` [omnivora.lua:Game.createMonsterType]
- `Game.createMonsterType("Rootthing Amber Shaper")` and `mType:register(monster)` [rootthing_amber_shaper.lua:Game.createMonsterType]
- `Game.createMonsterType("Rootthing Bug Tracker")` and `mType:register(monster)` [rootthing_bug_tracker.lua:Game.createMonsterType]
- `Game.createMonsterType("Rootthing Nutshell")` and `mType:register(monster)` [rootthing_nutshell.lua:Game.createMonsterType]
- `Game.createMonsterType("Spit Nettle")` and `mType:register(monster)` [spit_nettle.lua:Game.createMonsterType]
- `Game.createMonsterType("Stalking Stalk")` and `mType:register(monster)` [stalking_stalk.lua:Game.createMonsterType]
- `Game.createMonsterType("Swampling")` and `mType:register(monster)` [swampling.lua:Game.createMonsterType]
- `Game.createMonsterType("Wilting Leaf Golem")` and `mType:register(monster)` [wilting_leaf_golem.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bane_bringer.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bane_bringer.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [carniphila.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [carniphila.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [glooth_anemone.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [glooth_anemone.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [haunted_treeling.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [haunted_treeling.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [hideous_fungus.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [hideous_fungus.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [humongous_fungus.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [humongous_fungus.lua:monster.flags]

## Side Effects
- Registers monster type `Bane Bringer` into the global `Game` engine registry via `mType:register(monster)` [bane_bringer.lua:mType:register]
- Registers monster type `Carniphila` into the global `Game` engine registry via `mType:register(monster)` [carniphila.lua:mType:register]
- Registers monster type `Glooth Anemone` into the global `Game` engine registry via `mType:register(monster)` [glooth_anemone.lua:mType:register]
- Registers monster type `Haunted Treeling` into the global `Game` engine registry via `mType:register(monster)` [haunted_treeling.lua:mType:register]
- Registers monster type `Hideous Fungus` into the global `Game` engine registry via `mType:register(monster)` [hideous_fungus.lua:mType:register]
- Registers monster type `Humongous Fungus` into the global `Game` engine registry via `mType:register(monster)` [humongous_fungus.lua:mType:register]
- Registers monster type `Leaf Golem` into the global `Game` engine registry via `mType:register(monster)` [leaf_golem.lua:mType:register]
- Registers monster type `Omnivora` into the global `Game` engine registry via `mType:register(monster)` [omnivora.lua:mType:register]
- Registers monster type `Rootthing Amber Shaper` into the global `Game` engine registry via `mType:register(monster)` [rootthing_amber_shaper.lua:mType:register]
- Registers monster type `Rootthing Bug Tracker` into the global `Game` engine registry via `mType:register(monster)` [rootthing_bug_tracker.lua:mType:register]
- Registers monster type `Rootthing Nutshell` into the global `Game` engine registry via `mType:register(monster)` [rootthing_nutshell.lua:mType:register]
- Registers monster type `Spit Nettle` into the global `Game` engine registry via `mType:register(monster)` [spit_nettle.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
