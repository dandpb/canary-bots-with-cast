# In Service Of Yalahar

## Overview
Component package under `monster/quests/in_service_of_yalahar` containing 11 files (`azerus.lua`..`yalahari.lua`).

## Interface
- `Game.createMonsterType("Azerus")` and `mType:register(monster)` [azerus.lua:Game.createMonsterType]
- `Game.createMonsterType("Azerus2")` and `mType:register(monster)` [azerus2.lua:Game.createMonsterType]
- `Game.createMonsterType("Inky")` and `mType:register(monster)` [inky.lua:Game.createMonsterType]
- `Game.createMonsterType("Rift Brood")` and `mType:register(monster)` [rift_brood.lua:Game.createMonsterType]
- `Game.createMonsterType("Rift Lord")` and `mType:register(monster)` [rift_lord.lua:Game.createMonsterType]
- `Game.createMonsterType("Rift Phantom")` and `mType:register(monster)` [rift_phantom.lua:Game.createMonsterType]
- `Game.createMonsterType("Rift Scythe")` and `mType:register(monster)` [rift_scythe.lua:Game.createMonsterType]
- `Game.createMonsterType("Rift Worm")` and `mType:register(monster)` [rift_worm.lua:Game.createMonsterType]
- `Game.createMonsterType("Sharptooth")` and `mType:register(monster)` [sharptooth.lua:Game.createMonsterType]
- `Game.createMonsterType("Tormented Ghost")` and `mType:register(monster)` [tormented_ghost.lua:Game.createMonsterType]
- `Game.createMonsterType("Yalahari")` and `mType:register(monster)` [yalahari.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [azerus.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [azerus2.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [inky.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rift_brood.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rift_lord.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rift_phantom.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rift_scythe.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rift_worm.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [sharptooth.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [tormented_ghost.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [yalahari.lua:monster.flags]

## Side Effects
- Registers monster type `Azerus` into the global `Game` engine registry via `mType:register(monster)` [azerus.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [azerus.lua:monster.events]
- Registers monster type `Azerus2` into the global `Game` engine registry via `mType:register(monster)` [azerus2.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [azerus2.lua:monster.events]
- Registers monster type `Inky` into the global `Game` engine registry via `mType:register(monster)` [inky.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [inky.lua:monster.events]
- Registers monster type `Rift Brood` into the global `Game` engine registry via `mType:register(monster)` [rift_brood.lua:mType:register]
- Registers monster type `Rift Lord` into the global `Game` engine registry via `mType:register(monster)` [rift_lord.lua:mType:register]
- Registers monster type `Rift Phantom` into the global `Game` engine registry via `mType:register(monster)` [rift_phantom.lua:mType:register]
- Registers monster type `Rift Scythe` into the global `Game` engine registry via `mType:register(monster)` [rift_scythe.lua:mType:register]
- Registers monster type `Rift Worm` into the global `Game` engine registry via `mType:register(monster)` [rift_worm.lua:mType:register]
- Registers monster type `Sharptooth` into the global `Game` engine registry via `mType:register(monster)` [sharptooth.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
