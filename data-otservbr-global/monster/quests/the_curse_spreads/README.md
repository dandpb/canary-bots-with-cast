# The Curse Spreads

## Overview
Component package under `monster/quests/the_curse_spreads` containing 10 files (`black_vixen.lua`..`sharpclaw.lua`).

## Interface
- `Game.createMonsterType("Black Vixen")` and `mType:register(monster)` [black_vixen.lua:Game.createMonsterType]
- `Game.createMonsterType("Bloodback")` and `mType:register(monster)` [bloodback.lua:Game.createMonsterType]
- `Game.createMonsterType("Darkfang")` and `mType:register(monster)` [darkfang.lua:Game.createMonsterType]
- `Game.createMonsterType("Feroxa")` and `mType:register(monster)` [feroxa.lua:Game.createMonsterType]
- `Game.createMonsterType("Feroxa2")` and `mType:register(monster)` [feroxa2.lua:Game.createMonsterType]
- `Game.createMonsterType("Feroxa3")` and `mType:register(monster)` [feroxa3.lua:Game.createMonsterType]
- `Game.createMonsterType("Feroxa4")` and `mType:register(monster)` [feroxa4.lua:Game.createMonsterType]
- `Game.createMonsterType("Feroxa5")` and `mType:register(monster)` [feroxa5.lua:Game.createMonsterType]
- `Game.createMonsterType("Shadowpelt")` and `mType:register(monster)` [shadowpelt.lua:Game.createMonsterType]
- `Game.createMonsterType("Sharpclaw")` and `mType:register(monster)` [sharpclaw.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [black_vixen.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bloodback.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [darkfang.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [feroxa.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [feroxa2.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [feroxa3.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [feroxa4.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [feroxa5.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [shadowpelt.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [sharpclaw.lua:monster.flags]

## Side Effects
- Registers monster type `Black Vixen` into the global `Game` engine registry via `mType:register(monster)` [black_vixen.lua:mType:register]
- Registers monster type `Bloodback` into the global `Game` engine registry via `mType:register(monster)` [bloodback.lua:mType:register]
- Registers monster type `Darkfang` into the global `Game` engine registry via `mType:register(monster)` [darkfang.lua:mType:register]
- Registers monster type `Feroxa` into the global `Game` engine registry via `mType:register(monster)` [feroxa.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [feroxa.lua:monster.events]
- Registers monster type `Feroxa2` into the global `Game` engine registry via `mType:register(monster)` [feroxa2.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [feroxa2.lua:monster.events]
- Registers monster type `Feroxa3` into the global `Game` engine registry via `mType:register(monster)` [feroxa3.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [feroxa3.lua:monster.events]
- Registers monster type `Feroxa4` into the global `Game` engine registry via `mType:register(monster)` [feroxa4.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [feroxa4.lua:monster.events]
- Registers monster type `Feroxa5` into the global `Game` engine registry via `mType:register(monster)` [feroxa5.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
