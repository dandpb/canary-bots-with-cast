# Mysterious Ornate Chest

## Overview
Component package under `monster/quests/mysterious_ornate_chest` containing 5 files (`an_observer_eye.lua`..`ugly_monster.lua`).

## Interface
- `Game.createMonsterType("An Observer Eye")` and `mType:register(monster)` [an_observer_eye.lua:Game.createMonsterType]
- `Game.createMonsterType("An Observer Eye (imune)")` and `mType:register(monster)` [an_observer_eye_(imune).lua:Game.createMonsterType]
- `Game.createMonsterType("Reflection of Mawhawk")` and `mType:register(monster)` [reflection_of_mawhawk.lua:Game.createMonsterType]
- `Game.createMonsterType("Reflection of Obujos")` and `mType:register(monster)` [reflection_of_obujos.lua:Game.createMonsterType]
- `Game.createMonsterType("Ugly Monster")` and `mType:register(monster)` [ugly_monster.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [an_observer_eye.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [an_observer_eye_(imune).lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [reflection_of_mawhawk.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [reflection_of_obujos.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ugly_monster.lua:monster.flags]

## Side Effects
- Registers monster type `An Observer Eye` into the global `Game` engine registry via `mType:register(monster)` [an_observer_eye.lua:mType:register]
- Registers monster type `An Observer Eye (imune)` into the global `Game` engine registry via `mType:register(monster)` [an_observer_eye_(imune).lua:mType:register]
- Registers monster type `Reflection of Mawhawk` into the global `Game` engine registry via `mType:register(monster)` [reflection_of_mawhawk.lua:mType:register]
- Registers monster type `Reflection of Obujos` into the global `Game` engine registry via `mType:register(monster)` [reflection_of_obujos.lua:mType:register]
- Registers monster type `Ugly Monster` into the global `Game` engine registry via `mType:register(monster)` [ugly_monster.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [ugly_monster.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
