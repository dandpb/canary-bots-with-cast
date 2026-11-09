# Event Creatures

## Overview
Provides 14 direct files (`bones.lua`..`undead_minion.lua`) and 1 subdirectories under `monster/event_creatures`.

## Interface
- `Game.createMonsterType("Bones")` and `mType:register(monster)` [bones.lua:Game.createMonsterType]
- `Game.createMonsterType("Eclipse Knight")` and `mType:register(monster)` [eclipse_knight.lua:Game.createMonsterType]
- `Game.createMonsterType("Essence of Darkness")` and `mType:register(monster)` [essence_of_darkness.lua:Game.createMonsterType]
- `Game.createMonsterType("Fluffy")` and `mType:register(monster)` [fluffy.lua:Game.createMonsterType]
- `Game.createMonsterType("Grynch Clan Goblin")` and `mType:register(monster)` [grynch_clan_goblin.lua:Game.createMonsterType]
- `Game.createMonsterType("Hacker")` and `mType:register(monster)` [hacker.lua:Game.createMonsterType]
- `Game.createMonsterType("Minishabaal")` and `mType:register(monster)` [minishabaal.lua:Game.createMonsterType]
- `Game.createMonsterType("Party Skeleton")` and `mType:register(monster)` [party_skeleton.lua:Game.createMonsterType]
- `Game.createMonsterType("Pinata Dragon")` and `mType:register(monster)` [pinata_dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Primitive")` and `mType:register(monster)` [primitive.lua:Game.createMonsterType]
- `Game.createMonsterType("Spectral Scum")` and `mType:register(monster)` [spectral_scum.lua:Game.createMonsterType]
- `Game.createMonsterType("The Halloween Hare")` and `mType:register(monster)` [the_halloween_hare.lua:Game.createMonsterType]
- `Game.createMonsterType("The Mutated Pumpkin")` and `mType:register(monster)` [the_mutated_pumpkin.lua:Game.createMonsterType]
- `Game.createMonsterType("Undead Minion")` and `mType:register(monster)` [undead_minion.lua:Game.createMonsterType]
- [memory_creatures](./memory_creatures/README.md) - Component package under `monster/event_creatures/memory_creatures` containing 24 files (`memory_of_a_banshee.lua`..`memory_of_an_ogre.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bones.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [eclipse_knight.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [essence_of_darkness.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fluffy.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [grynch_clan_goblin.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [grynch_clan_goblin.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [hacker.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [minishabaal.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [party_skeleton.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [pinata_dragon.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [primitive.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [spectral_scum.lua:monster.flags]

## Side Effects
- Registers monster type `Bones` into the global `Game` engine registry via `mType:register(monster)` [bones.lua:mType:register]
- Registers monster type `Eclipse Knight` into the global `Game` engine registry via `mType:register(monster)` [eclipse_knight.lua:mType:register]
- Registers monster type `Essence of Darkness` into the global `Game` engine registry via `mType:register(monster)` [essence_of_darkness.lua:mType:register]
- Registers monster type `Fluffy` into the global `Game` engine registry via `mType:register(monster)` [fluffy.lua:mType:register]
- Registers monster type `Grynch Clan Goblin` into the global `Game` engine registry via `mType:register(monster)` [grynch_clan_goblin.lua:mType:register]
- Registers monster type `Hacker` into the global `Game` engine registry via `mType:register(monster)` [hacker.lua:mType:register]
- Registers monster type `Minishabaal` into the global `Game` engine registry via `mType:register(monster)` [minishabaal.lua:mType:register]
- Registers monster type `Party Skeleton` into the global `Game` engine registry via `mType:register(monster)` [party_skeleton.lua:mType:register]
- Registers monster type `Pinata Dragon` into the global `Game` engine registry via `mType:register(monster)` [pinata_dragon.lua:mType:register]
- Registers monster type `Primitive` into the global `Game` engine registry via `mType:register(monster)` [primitive.lua:mType:register]
- Registers monster type `Spectral Scum` into the global `Game` engine registry via `mType:register(monster)` [spectral_scum.lua:mType:register]
- Registers monster type `The Halloween Hare` into the global `Game` engine registry via `mType:register(monster)` [the_halloween_hare.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
