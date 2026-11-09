# Megalomania Room

## Overview
Component package under `monster/quests/soul_war/normal_monsters/megalomania_room` containing 4 files (`greater_splinter_of_madness.lua`..`necromantic_focus.lua`).

## Interface
- `Game.createMonsterType("Greater Splinter of Madness")` and `mType:register(monster)` [greater_splinter_of_madness.lua:Game.createMonsterType]
- `Game.createMonsterType("Lesser Splinter of Madness")` and `mType:register(monster)` [lesser_splinter_of_madness.lua:Game.createMonsterType]
- `Game.createMonsterType("Mighty Splinter of Madness")` and `mType:register(monster)` [mighty_splinter_of_madness.lua:Game.createMonsterType]
- `Game.createMonsterType("Necromantic Focus")` and `mType:register(monster)` [necromantic_focus.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [greater_splinter_of_madness.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lesser_splinter_of_madness.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mighty_splinter_of_madness.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [necromantic_focus.lua:monster.flags]

## Side Effects
- Registers monster type `Greater Splinter of Madness` into the global `Game` engine registry via `mType:register(monster)` [greater_splinter_of_madness.lua:mType:register]
- Registers monster type `Lesser Splinter of Madness` into the global `Game` engine registry via `mType:register(monster)` [lesser_splinter_of_madness.lua:mType:register]
- Registers monster type `Mighty Splinter of Madness` into the global `Game` engine registry via `mType:register(monster)` [mighty_splinter_of_madness.lua:mType:register]
- Registers monster type `Necromantic Focus` into the global `Game` engine registry via `mType:register(monster)` [necromantic_focus.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [necromantic_focus.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
