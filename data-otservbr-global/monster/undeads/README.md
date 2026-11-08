# Undeads

## Overview
Component package under `monster/undeads` containing 63 files (`ahau.lua`..`zombie.lua`).

## Interface
- Defines 63 script/configuration files (`ahau.lua` through `zombie.lua`) [ahau.lua]
- `Game.createMonsterType("Ahau")` and `mType:register(monster)` [ahau.lua:Game.createMonsterType]
- `Game.createMonsterType("Bane of Light")` and `mType:register(monster)` [bane_of_light.lua:Game.createMonsterType]
- `Game.createMonsterType("Banshee")` and `mType:register(monster)` [banshee.lua:Game.createMonsterType]
- `Game.createMonsterType("Betrayed Wraith")` and `mType:register(monster)` [betrayed_wraith.lua:Game.createMonsterType]
- `Game.createMonsterType("Blightwalker")` and `mType:register(monster)` [blightwalker.lua:Game.createMonsterType]
- `Game.createMonsterType("Blood Beast")` and `mType:register(monster)` [blood_beast.lua:Game.createMonsterType]
- `Game.createMonsterType("Bonebeast")` and `mType:register(monster)` [bonebeast.lua:Game.createMonsterType]
- `Game.createMonsterType("Burster Spectre")` and `mType:register(monster)` [burster_spectre.lua:Game.createMonsterType]
- `Game.createMonsterType("Crypt Shambler")` and `mType:register(monster)` [crypt_shambler.lua:Game.createMonsterType]
- `Game.createMonsterType("Crypt Warrior")` and `mType:register(monster)` [crypt_warrior.lua:Game.createMonsterType]
- `Game.createMonsterType("Cursed Ape")` and `mType:register(monster)` [cursed_ape.lua:Game.createMonsterType]
- `Game.createMonsterType("Cursed Prospector")` and `mType:register(monster)` [cursed_prospector.lua:Game.createMonsterType]
- `Game.createMonsterType("Death Priest")` and `mType:register(monster)` [death_priest.lua:Game.createMonsterType]
- `Game.createMonsterType("Demon Skeleton")` and `mType:register(monster)` [demon_skeleton.lua:Game.createMonsterType]
- `Game.createMonsterType("Elder Mummy")` and `mType:register(monster)` [elder_mummy.lua:Game.createMonsterType]
- `Game.createMonsterType("Evil Prospector")` and `mType:register(monster)` [evil_prospector.lua:Game.createMonsterType]
- `Game.createMonsterType("Falcon Knight")` and `mType:register(monster)` [falcon_knight.lua:Game.createMonsterType]
- `Game.createMonsterType("Falcon Paladin")` and `mType:register(monster)` [falcon_paladin.lua:Game.createMonsterType]
- `Game.createMonsterType("Flimsy Lost Soul")` and `mType:register(monster)` [flimsy_lost_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Freakish Lost Soul")` and `mType:register(monster)` [freakish_lost_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Gazer Spectre")` and `mType:register(monster)` [gazer_spectre.lua:Game.createMonsterType]
- `Game.createMonsterType("Ghost")` and `mType:register(monster)` [ghost.lua:Game.createMonsterType]
- `Game.createMonsterType("Ghoul")` and `mType:register(monster)` [ghoul.lua:Game.createMonsterType]
- `Game.createMonsterType("Grave Guard")` and `mType:register(monster)` [grave_guard.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ahau.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bane_of_light.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bane_of_light.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [banshee.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [banshee.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [betrayed_wraith.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [betrayed_wraith.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [blightwalker.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [blightwalker.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [blood_beast.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [blood_beast.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bonebeast.lua:monster.Bestiary]

## Side Effects
- Registers monster type `Ahau` into the global `Game` engine registry via `mType:register(monster)` [ahau.lua:mType:register]
- Registers monster type `Bane of Light` into the global `Game` engine registry via `mType:register(monster)` [bane_of_light.lua:mType:register]
- Registers monster type `Banshee` into the global `Game` engine registry via `mType:register(monster)` [banshee.lua:mType:register]
- Registers monster type `Betrayed Wraith` into the global `Game` engine registry via `mType:register(monster)` [betrayed_wraith.lua:mType:register]
- Registers monster type `Blightwalker` into the global `Game` engine registry via `mType:register(monster)` [blightwalker.lua:mType:register]
- Registers monster type `Blood Beast` into the global `Game` engine registry via `mType:register(monster)` [blood_beast.lua:mType:register]
- Registers monster type `Bonebeast` into the global `Game` engine registry via `mType:register(monster)` [bonebeast.lua:mType:register]
- Registers monster type `Burster Spectre` into the global `Game` engine registry via `mType:register(monster)` [burster_spectre.lua:mType:register]
- Registers monster type `Crypt Shambler` into the global `Game` engine registry via `mType:register(monster)` [crypt_shambler.lua:mType:register]
- Registers monster type `Crypt Warrior` into the global `Game` engine registry via `mType:register(monster)` [crypt_warrior.lua:mType:register]
- Registers monster type `Cursed Ape` into the global `Game` engine registry via `mType:register(monster)` [cursed_ape.lua:mType:register]
- Registers monster type `Cursed Prospector` into the global `Game` engine registry via `mType:register(monster)` [cursed_prospector.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
