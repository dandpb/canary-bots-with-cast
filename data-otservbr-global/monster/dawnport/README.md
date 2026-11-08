# Dawnport

## Overview
Component package under `monster/dawnport` containing 20 files (`brittle_skeleton.lua`..`woodling.lua`).

## Interface
- `Game.createMonsterType("Brittle Skeleton")` and `mType:register(monster)` [brittle_skeleton.lua:Game.createMonsterType]
- `Game.createMonsterType("Crazed Dwarf")` and `mType:register(monster)` [crazed_dwarf.lua:Game.createMonsterType]
- `Game.createMonsterType("Dawn Bat")` and `mType:register(monster)` [dawn_bat.lua:Game.createMonsterType]
- `Game.createMonsterType("Dawn Scorpion")` and `mType:register(monster)` [dawn_scorpion.lua:Game.createMonsterType]
- `Game.createMonsterType("Dawnfly")` and `mType:register(monster)` [dawnfly.lua:Game.createMonsterType]
- `Game.createMonsterType("Juvenile Cyclops")` and `mType:register(monster)` [juvenile_cyclops.lua:Game.createMonsterType]
- `Game.createMonsterType("Lesser Fire Devil")` and `mType:register(monster)` [lesser_fire_devil.lua:Game.createMonsterType]
- `Game.createMonsterType("Meadow Strider")` and `mType:register(monster)` [meadow_strider.lua:Game.createMonsterType]
- `Game.createMonsterType("Mountain Troll")` and `mType:register(monster)` [mountain_troll.lua:Game.createMonsterType]
- `Game.createMonsterType("Muglex Clan Assassin")` and `mType:register(monster)` [muglex_clan_assassin.lua:Game.createMonsterType]
- `Game.createMonsterType("Muglex Clan Footman")` and `mType:register(monster)` [muglex_clan_footman.lua:Game.createMonsterType]
- `Game.createMonsterType("Muglex Clan Scavenger")` and `mType:register(monster)` [muglex_clan_scavenger.lua:Game.createMonsterType]
- `Game.createMonsterType("Sacred Snake")` and `mType:register(monster)` [sacred_snake.lua:Game.createMonsterType]
- `Game.createMonsterType("Salamander Trainer")` and `mType:register(monster)` [salamander_trainer.lua:Game.createMonsterType]
- `Game.createMonsterType("Scar Tribe Shaman")` and `mType:register(monster)` [scar_tribe_shaman.lua:Game.createMonsterType]
- `Game.createMonsterType("Scar Tribe Warrior")` and `mType:register(monster)` [scar_tribe_warrior.lua:Game.createMonsterType]
- `Game.createMonsterType("Spidris Elite Summon")` and `mType:register(monster)` [spidris_elitesumom.lua:Game.createMonsterType]
- `Game.createMonsterType("Troll-Trained Salamander")` and `mType:register(monster)` [troll-trained_salamander.lua:Game.createMonsterType]
- `Game.createMonsterType("Troll Marauder")` and `mType:register(monster)` [troll_marauder.lua:Game.createMonsterType]
- `Game.createMonsterType("Woodling")` and `mType:register(monster)` [woodling.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brittle_skeleton.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [crazed_dwarf.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dawn_bat.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dawn_scorpion.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dawnfly.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [juvenile_cyclops.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lesser_fire_devil.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [meadow_strider.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mountain_troll.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [muglex_clan_assassin.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [muglex_clan_footman.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [muglex_clan_scavenger.lua:monster.flags]

## Side Effects
- Registers monster type `Brittle Skeleton` into the global `Game` engine registry via `mType:register(monster)` [brittle_skeleton.lua:mType:register]
- Registers monster type `Crazed Dwarf` into the global `Game` engine registry via `mType:register(monster)` [crazed_dwarf.lua:mType:register]
- Registers monster type `Dawn Bat` into the global `Game` engine registry via `mType:register(monster)` [dawn_bat.lua:mType:register]
- Registers monster type `Dawn Scorpion` into the global `Game` engine registry via `mType:register(monster)` [dawn_scorpion.lua:mType:register]
- Registers monster type `Dawnfly` into the global `Game` engine registry via `mType:register(monster)` [dawnfly.lua:mType:register]
- Registers monster type `Juvenile Cyclops` into the global `Game` engine registry via `mType:register(monster)` [juvenile_cyclops.lua:mType:register]
- Registers monster type `Lesser Fire Devil` into the global `Game` engine registry via `mType:register(monster)` [lesser_fire_devil.lua:mType:register]
- Registers monster type `Meadow Strider` into the global `Game` engine registry via `mType:register(monster)` [meadow_strider.lua:mType:register]
- Registers monster type `Mountain Troll` into the global `Game` engine registry via `mType:register(monster)` [mountain_troll.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [mountain_troll.lua:monster.events]
- Registers monster type `Muglex Clan Assassin` into the global `Game` engine registry via `mType:register(monster)` [muglex_clan_assassin.lua:mType:register]
- Registers monster type `Muglex Clan Footman` into the global `Game` engine registry via `mType:register(monster)` [muglex_clan_footman.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
