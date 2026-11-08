# Bosses

## Overview
Component package under `monster/quests/grave_danger/bosses` containing 8 files (`count_vlarkorth.lua`..`sir_nictros.lua`).

## Interface
- `Game.createMonsterType("Count Vlarkorth")` and `mType:register(monster)` [count_vlarkorth.lua:Game.createMonsterType]
- `Game.createMonsterType("Duke Krule")` and `mType:register(monster)` [duke_krule.lua:Game.createMonsterType]
- `Game.createMonsterType("Earl Osam")` and `mType:register(monster)` [earl_osam.lua:Game.createMonsterType]
- `Game.createMonsterType("King Zelos")` and `mType:register(monster)` [king_zelos.lua:Game.createMonsterType]
- `Game.createMonsterType("Lord Azaram")` and `mType:register(monster)` [lord_azaram.lua:Game.createMonsterType]
- `Game.createMonsterType("Scarlett Etzel")` and `mType:register(monster)` [scarlett_etzel.lua:Game.createMonsterType]
- `Game.createMonsterType("Sir Baeloc")` and `mType:register(monster)` [sir_baeloc.lua:Game.createMonsterType]
- `Game.createMonsterType("Sir Nictros")` and `mType:register(monster)` [sir_nictros.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [count_vlarkorth.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [duke_krule.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [earl_osam.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [king_zelos.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lord_azaram.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [scarlett_etzel.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [sir_baeloc.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [sir_nictros.lua:monster.flags]

## Side Effects
- Registers monster type `Count Vlarkorth` into the global `Game` engine registry via `mType:register(monster)` [count_vlarkorth.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [count_vlarkorth.lua:monster.events]
- Registers monster type `Duke Krule` into the global `Game` engine registry via `mType:register(monster)` [duke_krule.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [duke_krule.lua:monster.events]
- Registers monster type `Earl Osam` into the global `Game` engine registry via `mType:register(monster)` [earl_osam.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [earl_osam.lua:monster.events]
- Registers monster type `King Zelos` into the global `Game` engine registry via `mType:register(monster)` [king_zelos.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [king_zelos.lua:monster.events]
- Registers monster type `Lord Azaram` into the global `Game` engine registry via `mType:register(monster)` [lord_azaram.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [lord_azaram.lua:monster.events]
- Registers monster type `Scarlett Etzel` into the global `Game` engine registry via `mType:register(monster)` [scarlett_etzel.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [scarlett_etzel.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
