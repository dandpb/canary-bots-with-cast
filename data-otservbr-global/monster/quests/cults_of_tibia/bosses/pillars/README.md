# Pillars

## Overview
Component package under `monster/quests/cults_of_tibia/bosses/pillars` containing 7 files (`containment_crystal.lua`..`pillar_of_summoning.lua`).

## Interface
- `Game.createMonsterType("Containment Crystal")` and `mType:register(monster)` [containment_crystal.lua:Game.createMonsterType]
- `Game.createMonsterType("Destroyed Pillar")` and `mType:register(monster)` [destroyed_pillar.lua:Game.createMonsterType]
- `Game.createMonsterType("Pillar of Death")` and `mType:register(monster)` [pillar_of_death.lua:Game.createMonsterType]
- `Game.createMonsterType("Pillar of Draining")` and `mType:register(monster)` [pillar_of_draining.lua:Game.createMonsterType]
- `Game.createMonsterType("Pillar of Healing")` and `mType:register(monster)` [pillar_of_healing.lua:Game.createMonsterType]
- `Game.createMonsterType("Pillar of Protection")` and `mType:register(monster)` [pillar_of_protection.lua:Game.createMonsterType]
- `Game.createMonsterType("Pillar of Summoning")` and `mType:register(monster)` [pillar_of_summoning.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [containment_crystal.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [destroyed_pillar.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [pillar_of_death.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [pillar_of_draining.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [pillar_of_healing.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [pillar_of_protection.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [pillar_of_summoning.lua:monster.flags]

## Side Effects
- Registers monster type `Containment Crystal` into the global `Game` engine registry via `mType:register(monster)` [containment_crystal.lua:mType:register]
- Registers monster type `Destroyed Pillar` into the global `Game` engine registry via `mType:register(monster)` [destroyed_pillar.lua:mType:register]
- Registers monster type `Pillar of Death` into the global `Game` engine registry via `mType:register(monster)` [pillar_of_death.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [pillar_of_death.lua:monster.events]
- Registers monster type `Pillar of Draining` into the global `Game` engine registry via `mType:register(monster)` [pillar_of_draining.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [pillar_of_draining.lua:monster.events]
- Registers monster type `Pillar of Healing` into the global `Game` engine registry via `mType:register(monster)` [pillar_of_healing.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [pillar_of_healing.lua:monster.events]
- Registers monster type `Pillar of Protection` into the global `Game` engine registry via `mType:register(monster)` [pillar_of_protection.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [pillar_of_protection.lua:monster.events]
- Registers monster type `Pillar of Summoning` into the global `Game` engine registry via `mType:register(monster)` [pillar_of_summoning.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [pillar_of_summoning.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
