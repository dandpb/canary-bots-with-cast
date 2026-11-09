# The New Frontier

## Overview
Component package under `monster/quests/the_new_frontier` containing 15 files (`baron_brute.lua`..`tremorak.lua`).

## Interface
- `Game.createMonsterType("Baron Brute")` and `mType:register(monster)` [baron_brute.lua:Game.createMonsterType]
- `Game.createMonsterType("Coldheart")` and `mType:register(monster)` [coldheart.lua:Game.createMonsterType]
- `Game.createMonsterType("Doomhowl")` and `mType:register(monster)` [doomhowl.lua:Game.createMonsterType]
- `Game.createMonsterType("Dreadwing")` and `mType:register(monster)` [dreadwing.lua:Game.createMonsterType]
- `Game.createMonsterType("Fatality")` and `mType:register(monster)` [fatality.lua:Game.createMonsterType]
- `Game.createMonsterType("Haunter")` and `mType:register(monster)` [haunter.lua:Game.createMonsterType]
- `Game.createMonsterType("Incineron")` and `mType:register(monster)` [incineron.lua:Game.createMonsterType]
- `Game.createMonsterType("Menace")` and `mType:register(monster)` [menace.lua:Game.createMonsterType]
- Lua script module `mooh'tah_master.lua` [mooh'tah_master.lua:module]
- `Game.createMonsterType("Rocko")` and `mType:register(monster)` [rocko.lua:Game.createMonsterType]
- `Game.createMonsterType("Shard of Corruption")` and `mType:register(monster)` [shard_of_corruption.lua:Game.createMonsterType]
- `Game.createMonsterType("The Axeorcist")` and `mType:register(monster)` [the_axeorcist.lua:Game.createMonsterType]
- `Game.createMonsterType("The Dreadorian")` and `mType:register(monster)` [the_dreadorian.lua:Game.createMonsterType]
- `Game.createMonsterType("Tirecz")` and `mType:register(monster)` [tirecz.lua:Game.createMonsterType]
- `Game.createMonsterType("Tremorak")` and `mType:register(monster)` [tremorak.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [baron_brute.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [coldheart.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [doomhowl.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dreadwing.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fatality.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [haunter.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [incineron.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [menace.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rocko.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [shard_of_corruption.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_axeorcist.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_dreadorian.lua:monster.flags]

## Side Effects
- Registers monster type `Baron Brute` into the global `Game` engine registry via `mType:register(monster)` [baron_brute.lua:mType:register]
- Registers monster type `Coldheart` into the global `Game` engine registry via `mType:register(monster)` [coldheart.lua:mType:register]
- Registers monster type `Doomhowl` into the global `Game` engine registry via `mType:register(monster)` [doomhowl.lua:mType:register]
- Registers monster type `Dreadwing` into the global `Game` engine registry via `mType:register(monster)` [dreadwing.lua:mType:register]
- Registers monster type `Fatality` into the global `Game` engine registry via `mType:register(monster)` [fatality.lua:mType:register]
- Registers monster type `Haunter` into the global `Game` engine registry via `mType:register(monster)` [haunter.lua:mType:register]
- Registers monster type `Incineron` into the global `Game` engine registry via `mType:register(monster)` [incineron.lua:mType:register]
- Registers monster type `Menace` into the global `Game` engine registry via `mType:register(monster)` [menace.lua:mType:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [mooh'tah_master.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [mooh'tah_master.lua:Game]
- Registers monster type `Rocko` into the global `Game` engine registry via `mType:register(monster)` [rocko.lua:mType:register]
- Registers monster type `Shard of Corruption` into the global `Game` engine registry via `mType:register(monster)` [shard_of_corruption.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
