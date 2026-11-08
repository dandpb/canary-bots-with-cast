# Warlord

## Overview
Component package under `monster/quests/svargrond_arena/warlord` containing 10 files (`darakan_the_executioner.lua`..`webster.lua`).

## Interface
- `Game.createMonsterType("Darakan the Executioner")` and `mType:register(monster)` [darakan_the_executioner.lua:Game.createMonsterType]
- `Game.createMonsterType("Deathbringer")` and `mType:register(monster)` [deathbringer.lua:Game.createMonsterType]
- Lua script module `fallen_mooh'tah_master_ghar.lua` [fallen_mooh'tah_master_ghar.lua:module]
- `Game.createMonsterType("Gnorre Chyllson")` and `mType:register(monster)` [gnorre_chyllson.lua:Game.createMonsterType]
- `Game.createMonsterType("Norgle Glacierbeard")` and `mType:register(monster)` [norgle_glacierbeard.lua:Game.createMonsterType]
- `Game.createMonsterType("Svoren the Mad")` and `mType:register(monster)` [svoren_the_mad.lua:Game.createMonsterType]
- `Game.createMonsterType("The Masked Marauder")` and `mType:register(monster)` [the_masked_marauder.lua:Game.createMonsterType]
- `Game.createMonsterType("The Obliverator")` and `mType:register(monster)` [the_obliverator.lua:Game.createMonsterType]
- `Game.createMonsterType("The Pit Lord")` and `mType:register(monster)` [the_pit_lord.lua:Game.createMonsterType]
- `Game.createMonsterType("Webster")` and `mType:register(monster)` [webster.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [darakan_the_executioner.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [deathbringer.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [gnorre_chyllson.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [norgle_glacierbeard.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [svoren_the_mad.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_masked_marauder.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_obliverator.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_pit_lord.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [webster.lua:monster.flags]

## Side Effects
- Registers monster type `Darakan the Executioner` into the global `Game` engine registry via `mType:register(monster)` [darakan_the_executioner.lua:mType:register]
- Registers monster type `Deathbringer` into the global `Game` engine registry via `mType:register(monster)` [deathbringer.lua:mType:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [fallen_mooh'tah_master_ghar.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [fallen_mooh'tah_master_ghar.lua:Game]
- Registers monster type `Gnorre Chyllson` into the global `Game` engine registry via `mType:register(monster)` [gnorre_chyllson.lua:mType:register]
- Registers monster type `Norgle Glacierbeard` into the global `Game` engine registry via `mType:register(monster)` [norgle_glacierbeard.lua:mType:register]
- Registers monster type `Svoren the Mad` into the global `Game` engine registry via `mType:register(monster)` [svoren_the_mad.lua:mType:register]
- Registers monster type `The Masked Marauder` into the global `Game` engine registry via `mType:register(monster)` [the_masked_marauder.lua:mType:register]
- Registers monster type `The Obliverator` into the global `Game` engine registry via `mType:register(monster)` [the_obliverator.lua:mType:register]
- Registers monster type `The Pit Lord` into the global `Game` engine registry via `mType:register(monster)` [the_pit_lord.lua:mType:register]
- Registers monster type `Webster` into the global `Game` engine registry via `mType:register(monster)` [webster.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
