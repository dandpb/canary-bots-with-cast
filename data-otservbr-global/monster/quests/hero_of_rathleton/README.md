# Hero Of Rathleton

## Overview
Component package under `monster/quests/hero_of_rathleton` containing 13 files (`deep_terror.lua`..`weakened_glooth_horror.lua`).

## Interface
- `Game.createMonsterType("Deep Terror")` and `mType:register(monster)` [deep_terror.lua:Game.createMonsterType]
- `Game.createMonsterType("Empowered Glooth Horror")` and `mType:register(monster)` [empowered_glooth_horror.lua:Game.createMonsterType]
- `Game.createMonsterType("Energy Pulse")` and `mType:register(monster)` [energy_pulse.lua:Game.createMonsterType]
- `Game.createMonsterType("Feeble Glooth Horror")` and `mType:register(monster)` [feeble_glooth_horror.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth-Generator")` and `mType:register(monster)` [glooth-generator.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth Horror")` and `mType:register(monster)` [glooth_horror.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth Masher")` and `mType:register(monster)` [glooth_masher.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth Slasher")` and `mType:register(monster)` [glooth_slasher.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth Trasher")` and `mType:register(monster)` [glooth_trasher.lua:Game.createMonsterType]
- `Game.createMonsterType("Professor Maxxen")` and `mType:register(monster)` [professor_maxxen.lua:Game.createMonsterType]
- `Game.createMonsterType("Strong Glooth Horror")` and `mType:register(monster)` [strong_glooth_horror.lua:Game.createMonsterType]
- `Game.createMonsterType("Tentacle of the Deep Terror")` and `mType:register(monster)` [tentacle_of_the_deep_terror.lua:Game.createMonsterType]
- `Game.createMonsterType("Weakened Glooth Horror")` and `mType:register(monster)` [weakened_glooth_horror.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [deep_terror.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [empowered_glooth_horror.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [energy_pulse.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [feeble_glooth_horror.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [glooth-generator.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [glooth_horror.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [glooth_masher.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [glooth_slasher.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [glooth_trasher.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [professor_maxxen.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [strong_glooth_horror.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [tentacle_of_the_deep_terror.lua:monster.flags]

## Side Effects
- Registers monster type `Deep Terror` into the global `Game` engine registry via `mType:register(monster)` [deep_terror.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [deep_terror.lua:monster.events]
- Registers monster type `Empowered Glooth Horror` into the global `Game` engine registry via `mType:register(monster)` [empowered_glooth_horror.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [empowered_glooth_horror.lua:monster.events]
- Registers monster type `Energy Pulse` into the global `Game` engine registry via `mType:register(monster)` [energy_pulse.lua:mType:register]
- Registers monster type `Feeble Glooth Horror` into the global `Game` engine registry via `mType:register(monster)` [feeble_glooth_horror.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [feeble_glooth_horror.lua:monster.events]
- Registers monster type `Glooth-Generator` into the global `Game` engine registry via `mType:register(monster)` [glooth-generator.lua:mType:register]
- Registers monster type `Glooth Horror` into the global `Game` engine registry via `mType:register(monster)` [glooth_horror.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [glooth_horror.lua:monster.events]
- Registers monster type `Glooth Masher` into the global `Game` engine registry via `mType:register(monster)` [glooth_masher.lua:mType:register]
- Registers monster type `Glooth Slasher` into the global `Game` engine registry via `mType:register(monster)` [glooth_slasher.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
