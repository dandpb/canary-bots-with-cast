# The Inquisition

## Overview
Component package under `monster/quests/the_inquisition` containing 13 files (`a_carved_stone_tile.lua`..`zugurosh.lua`).

## Interface
- `Game.createMonsterType("a carved stone tile")` and `mType:register(monster)` [a_carved_stone_tile.lua:Game.createMonsterType]
- `Game.createMonsterType("Annihilon")` and `mType:register(monster)` [annihilon.lua:Game.createMonsterType]
- `Game.createMonsterType("Dreadbeast")` and `mType:register(monster)` [dreadbeast.lua:Game.createMonsterType]
- `Game.createMonsterType("Eye of the Seven")` and `mType:register(monster)` [eye_of_the_seven.lua:Game.createMonsterType]
- `Game.createMonsterType("Golgordan")` and `mType:register(monster)` [golgordan.lua:Game.createMonsterType]
- `Game.createMonsterType("Hellgorak")` and `mType:register(monster)` [hellgorak.lua:Game.createMonsterType]
- `Game.createMonsterType("Latrivan")` and `mType:register(monster)` [latrivan.lua:Game.createMonsterType]
- `Game.createMonsterType("Madareth")` and `mType:register(monster)` [madareth.lua:Game.createMonsterType]
- `Game.createMonsterType("The Count")` and `mType:register(monster)` [the_count.lua:Game.createMonsterType]
- `Game.createMonsterType("The Weakened Count")` and `mType:register(monster)` [the_weakened_count.lua:Game.createMonsterType]
- `Game.createMonsterType("Ungreez")` and `mType:register(monster)` [ungreez.lua:Game.createMonsterType]
- `Game.createMonsterType("Ushuriel")` and `mType:register(monster)` [ushuriel.lua:Game.createMonsterType]
- `Game.createMonsterType("Zugurosh")` and `mType:register(monster)` [zugurosh.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [a_carved_stone_tile.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [annihilon.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dreadbeast.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [eye_of_the_seven.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [golgordan.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [hellgorak.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [latrivan.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [madareth.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_count.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_weakened_count.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ungreez.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ushuriel.lua:monster.flags]

## Side Effects
- Registers monster type `a carved stone tile` into the global `Game` engine registry via `mType:register(monster)` [a_carved_stone_tile.lua:mType:register]
- Registers monster type `Annihilon` into the global `Game` engine registry via `mType:register(monster)` [annihilon.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [annihilon.lua:monster.events]
- Registers monster type `Dreadbeast` into the global `Game` engine registry via `mType:register(monster)` [dreadbeast.lua:mType:register]
- Registers monster type `Eye of the Seven` into the global `Game` engine registry via `mType:register(monster)` [eye_of_the_seven.lua:mType:register]
- Registers monster type `Golgordan` into the global `Game` engine registry via `mType:register(monster)` [golgordan.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [golgordan.lua:monster.events]
- Registers monster type `Hellgorak` into the global `Game` engine registry via `mType:register(monster)` [hellgorak.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [hellgorak.lua:monster.events]
- Registers monster type `Latrivan` into the global `Game` engine registry via `mType:register(monster)` [latrivan.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [latrivan.lua:monster.events]
- Registers monster type `Madareth` into the global `Game` engine registry via `mType:register(monster)` [madareth.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
