# Bosses

## Overview
Component package under `monster/quests/the_dream_courts/bosses` containing 7 files (`alptramun.lua`..`the_nightmare_beast.lua`).

## Interface
- `Game.createMonsterType("Alptramun")` and `mType:register(monster)` [alptramun.lua:Game.createMonsterType]
- `Game.createMonsterType("Faceless Bane")` and `mType:register(monster)` [faceless_bane.lua:Game.createMonsterType]
- `Game.createMonsterType("Izcandar the Banished")` and `mType:register(monster)` [izcandar_the_banished.lua:Game.createMonsterType]
- `Game.createMonsterType("Malofur Mangrinder")` and `mType:register(monster)` [malofur_mangrinder.lua:Game.createMonsterType]
- `Game.createMonsterType("Maxxenius")` and `mType:register(monster)` [maxxenius.lua:Game.createMonsterType]
- `Game.createMonsterType("Plagueroot")` and `mType:register(monster)` [plagueroot.lua:Game.createMonsterType]
- `Game.createMonsterType("The Nightmare Beast")` and `mType:register(monster)` [the_nightmare_beast.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [alptramun.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [faceless_bane.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [izcandar_the_banished.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [malofur_mangrinder.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [maxxenius.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [plagueroot.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_nightmare_beast.lua:monster.flags]

## Side Effects
- Registers monster type `Alptramun` into the global `Game` engine registry via `mType:register(monster)` [alptramun.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [alptramun.lua:monster.events]
- Registers monster type `Faceless Bane` into the global `Game` engine registry via `mType:register(monster)` [faceless_bane.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [faceless_bane.lua:monster.events]
- Registers monster type `Izcandar the Banished` into the global `Game` engine registry via `mType:register(monster)` [izcandar_the_banished.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [izcandar_the_banished.lua:monster.events]
- Registers monster type `Malofur Mangrinder` into the global `Game` engine registry via `mType:register(monster)` [malofur_mangrinder.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [malofur_mangrinder.lua:monster.events]
- Registers monster type `Maxxenius` into the global `Game` engine registry via `mType:register(monster)` [maxxenius.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [maxxenius.lua:monster.events]
- Registers monster type `Plagueroot` into the global `Game` engine registry via `mType:register(monster)` [plagueroot.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [plagueroot.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
