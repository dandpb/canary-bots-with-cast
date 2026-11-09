# A Pirates Tail Quest

## Overview
Component package under `monster/quests/a_pirates_tail_quest` containing 2 files (`ratmiral_blackwhiskers.lua`..`tentuglys_head.lua`).

## Interface
- `Game.createMonsterType("Ratmiral Blackwhiskers")` and `mType:register(monster)` [ratmiral_blackwhiskers.lua:Game.createMonsterType]
- Lua script module `tentuglys_head.lua` [tentuglys_head.lua:module]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ratmiral_blackwhiskers.lua:monster.flags]

## Side Effects
- Registers monster type `Ratmiral Blackwhiskers` into the global `Game` engine registry via `mType:register(monster)` [ratmiral_blackwhiskers.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [ratmiral_blackwhiskers.lua:monster.events]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [tentuglys_head.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [tentuglys_head.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
