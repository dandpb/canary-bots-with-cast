# Feaster Of Souls

## Overview
Component package under `monster/quests/feaster_of_souls` containing 9 files (`brother_worm.lua`..`wormling.lua`).

## Interface
- `Game.createMonsterType("Brother Worm")` and `mType:register(monster)` [brother_worm.lua:Game.createMonsterType]
- `Game.createMonsterType("Irgix The Flimsy")` and `mType:register(monster)` [irgix_the_flimsy.lua:Game.createMonsterType]
- `Game.createMonsterType("The Dread Maiden")` and `mType:register(monster)` [the_dread_maiden.lua:Game.createMonsterType]
- `Game.createMonsterType("The Fear Feaster")` and `mType:register(monster)` [the_fear_feaster.lua:Game.createMonsterType]
- `Game.createMonsterType("The Pale Worm")` and `mType:register(monster)` [the_pale_worm.lua:Game.createMonsterType]
- `Game.createMonsterType("The Unwelcome")` and `mType:register(monster)` [the_unwelcome.lua:Game.createMonsterType]
- `Game.createMonsterType("Unaz the Mean")` and `mType:register(monster)` [unaz_the_mean.lua:Game.createMonsterType]
- `Game.createMonsterType("Vok the Freakish")` and `mType:register(monster)` [vok_the_freakish.lua:Game.createMonsterType]
- `Game.createMonsterType("Wormling")` and `mType:register(monster)` [wormling.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brother_worm.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [irgix_the_flimsy.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_dread_maiden.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_fear_feaster.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_pale_worm.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_unwelcome.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [unaz_the_mean.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [vok_the_freakish.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [wormling.lua:monster.flags]

## Side Effects
- Registers monster type `Brother Worm` into the global `Game` engine registry via `mType:register(monster)` [brother_worm.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [brother_worm.lua:monster.events]
- Registers monster type `Irgix The Flimsy` into the global `Game` engine registry via `mType:register(monster)` [irgix_the_flimsy.lua:mType:register]
- Registers monster type `The Dread Maiden` into the global `Game` engine registry via `mType:register(monster)` [the_dread_maiden.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [the_dread_maiden.lua:monster.events]
- Registers monster type `The Fear Feaster` into the global `Game` engine registry via `mType:register(monster)` [the_fear_feaster.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [the_fear_feaster.lua:monster.events]
- Registers monster type `The Pale Worm` into the global `Game` engine registry via `mType:register(monster)` [the_pale_worm.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [the_pale_worm.lua:monster.events]
- Registers monster type `The Unwelcome` into the global `Game` engine registry via `mType:register(monster)` [the_unwelcome.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [the_unwelcome.lua:monster.events]
- Registers monster type `Unaz the Mean` into the global `Game` engine registry via `mType:register(monster)` [unaz_the_mean.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
