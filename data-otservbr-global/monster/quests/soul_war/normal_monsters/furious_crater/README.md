# Furious Crater

## Overview
Component package under `monster/quests/soul_war/normal_monsters/furious_crater` containing 5 files (`a_greedy_eye.lua`..`vibrant_phantom.lua`).

## Interface
- `Game.createMonsterType("A Greedy Eye")` and `mType:register(monster)` [a_greedy_eye.lua:Game.createMonsterType]
- `Game.createMonsterType("Cloak of Terror")` and `mType:register(monster)` [cloak_of_terror.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [cloak_of_terror.lua:mType.onThink]
- `Game.createMonsterType("Courage Leech")` and `mType:register(monster)` [courage_leech.lua:Game.createMonsterType]
- `Game.createMonsterType("Poor Soul")` and `mType:register(monster)` [poor_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Vibrant Phantom")` and `mType:register(monster)` [vibrant_phantom.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [a_greedy_eye.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [cloak_of_terror.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cloak_of_terror.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [courage_leech.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [courage_leech.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [poor_soul.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [vibrant_phantom.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [vibrant_phantom.lua:monster.flags]

## Side Effects
- Registers monster type `A Greedy Eye` into the global `Game` engine registry via `mType:register(monster)` [a_greedy_eye.lua:mType:register]
- Registers monster type `Cloak of Terror` into the global `Game` engine registry via `mType:register(monster)` [cloak_of_terror.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [cloak_of_terror.lua:monster.events]
- Registers monster type `Courage Leech` into the global `Game` engine registry via `mType:register(monster)` [courage_leech.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [courage_leech.lua:monster.events]
- Registers monster type `Poor Soul` into the global `Game` engine registry via `mType:register(monster)` [poor_soul.lua:mType:register]
- Registers monster type `Vibrant Phantom` into the global `Game` engine registry via `mType:register(monster)` [vibrant_phantom.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [vibrant_phantom.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
