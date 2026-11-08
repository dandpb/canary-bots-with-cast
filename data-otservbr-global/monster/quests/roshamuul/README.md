# Roshamuul

## Overview
Component package under `monster/quests/roshamuul` containing 9 files (`bad_dream.lua`..`terofar.lua`).

## Interface
- `Game.createMonsterType("Bad Dream")` and `mType:register(monster)` [bad_dream.lua:Game.createMonsterType]
- `Game.createMonsterType("Flame of Omrafir")` and `mType:register(monster)` [flame_of_omrafir.lua:Game.createMonsterType]
- Lua script module `gaz'haragoth.lua` [gaz'haragoth.lua:module]
- `Game.createMonsterType("Horadron")` and `mType:register(monster)` [horadron.lua:Game.createMonsterType]
- Lua script module `minion_of_gaz'haragoth.lua` [minion_of_gaz'haragoth.lua:module]
- Lua script module `nightmare_of_gaz'haragoth.lua` [nightmare_of_gaz'haragoth.lua:module]
- `Game.createMonsterType("Omrafir")` and `mType:register(monster)` [omrafir.lua:Game.createMonsterType]
- `Game.createMonsterType("Prince Drazzak")` and `mType:register(monster)` [prince_drazzak.lua:Game.createMonsterType]
- `Game.createMonsterType("Terofar")` and `mType:register(monster)` [terofar.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bad_dream.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [flame_of_omrafir.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [horadron.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [omrafir.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [prince_drazzak.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [terofar.lua:monster.flags]

## Side Effects
- Registers monster type `Bad Dream` into the global `Game` engine registry via `mType:register(monster)` [bad_dream.lua:mType:register]
- Registers monster type `Flame of Omrafir` into the global `Game` engine registry via `mType:register(monster)` [flame_of_omrafir.lua:mType:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [gaz'haragoth.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [gaz'haragoth.lua:Game]
- Registers monster type `Horadron` into the global `Game` engine registry via `mType:register(monster)` [horadron.lua:mType:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [minion_of_gaz'haragoth.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [minion_of_gaz'haragoth.lua:Game]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [nightmare_of_gaz'haragoth.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [nightmare_of_gaz'haragoth.lua:Game]
- Registers monster type `Omrafir` into the global `Game` engine registry via `mType:register(monster)` [omrafir.lua:mType:register]
- Registers monster type `Prince Drazzak` into the global `Game` engine registry via `mType:register(monster)` [prince_drazzak.lua:mType:register]
- Registers monster type `Terofar` into the global `Game` engine registry via `mType:register(monster)` [terofar.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
