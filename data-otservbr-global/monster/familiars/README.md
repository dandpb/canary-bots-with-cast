# Familiars

## Overview
Component package under `monster/familiars` containing 5 files (`druid_familiar.lua`..`sorcerer_familiar.lua`).

## Interface
- `Game.createMonsterType("Druid familiar")` and `mType:register(monster)` [druid_familiar.lua:Game.createMonsterType]
- `Game.createMonsterType("Knight familiar")` and `mType:register(monster)` [knight_familiar.lua:Game.createMonsterType]
- `Game.createMonsterType("Monk familiar")` and `mType:register(monster)` [monk_familiar.lua:Game.createMonsterType]
- `Game.createMonsterType("Paladin familiar")` and `mType:register(monster)` [paladin_familiar.lua:Game.createMonsterType]
- `Game.createMonsterType("Sorcerer familiar")` and `mType:register(monster)` [sorcerer_familiar.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [druid_familiar.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [knight_familiar.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [monk_familiar.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [paladin_familiar.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [sorcerer_familiar.lua:monster.flags]

## Side Effects
- Registers monster type `Druid familiar` into the global `Game` engine registry via `mType:register(monster)` [druid_familiar.lua:mType:register]
- Registers monster type `Knight familiar` into the global `Game` engine registry via `mType:register(monster)` [knight_familiar.lua:mType:register]
- Registers monster type `Monk familiar` into the global `Game` engine registry via `mType:register(monster)` [monk_familiar.lua:mType:register]
- Registers monster type `Paladin familiar` into the global `Game` engine registry via `mType:register(monster)` [paladin_familiar.lua:mType:register]
- Registers monster type `Sorcerer familiar` into the global `Game` engine registry via `mType:register(monster)` [sorcerer_familiar.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
