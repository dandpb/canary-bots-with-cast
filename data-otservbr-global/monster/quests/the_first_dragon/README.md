# The First Dragon

## Overview
Provides 9 direct files (`angry_plant.lua`..`unbeatable_dragon.lua`) and 1 subdirectories under `monster/quests/the_first_dragon`.

## Interface
- `Game.createMonsterType("Angry Plant")` and `mType:register(monster)` [angry_plant.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragon Essence")` and `mType:register(monster)` [dragon_essence.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragon Warden")` and `mType:register(monster)` [dragon_warden.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragon Wrath")` and `mType:register(monster)` [dragon_wrath.lua:Game.createMonsterType]
- `Game.createMonsterType("Haunted Dragon")` and `mType:register(monster)` [haunted_dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Ice Dragon")` and `mType:register(monster)` [ice_dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Somewhat Beatable")` and `mType:register(monster)` [somewhat_beatable.lua:Game.createMonsterType]
- `Game.createMonsterType("Spirit of Fertility")` and `mType:register(monster)` [spirit_of_fertility.lua:Game.createMonsterType]
- `Game.createMonsterType("Unbeatable Dragon")` and `mType:register(monster)` [unbeatable_dragon.lua:Game.createMonsterType]
- [bosses](./bosses/README.md) - Component package under `monster/quests/the_first_dragon/bosses` containing 5 files (`fallen_challenger.lua`..`zorvorax.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [angry_plant.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragon_essence.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragon_warden.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragon_wrath.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [haunted_dragon.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [haunted_dragon.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [ice_dragon.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ice_dragon.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [somewhat_beatable.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [spirit_of_fertility.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [unbeatable_dragon.lua:monster.flags]

## Side Effects
- Registers monster type `Angry Plant` into the global `Game` engine registry via `mType:register(monster)` [angry_plant.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [angry_plant.lua:monster.events]
- Registers monster type `Dragon Essence` into the global `Game` engine registry via `mType:register(monster)` [dragon_essence.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [dragon_essence.lua:monster.events]
- Registers monster type `Dragon Warden` into the global `Game` engine registry via `mType:register(monster)` [dragon_warden.lua:mType:register]
- Registers monster type `Dragon Wrath` into the global `Game` engine registry via `mType:register(monster)` [dragon_wrath.lua:mType:register]
- Registers monster type `Haunted Dragon` into the global `Game` engine registry via `mType:register(monster)` [haunted_dragon.lua:mType:register]
- Registers monster type `Ice Dragon` into the global `Game` engine registry via `mType:register(monster)` [ice_dragon.lua:mType:register]
- Registers monster type `Somewhat Beatable` into the global `Game` engine registry via `mType:register(monster)` [somewhat_beatable.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [somewhat_beatable.lua:monster.events]
- Registers monster type `Spirit of Fertility` into the global `Game` engine registry via `mType:register(monster)` [spirit_of_fertility.lua:mType:register]
- Registers monster type `Unbeatable Dragon` into the global `Game` engine registry via `mType:register(monster)` [unbeatable_dragon.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
