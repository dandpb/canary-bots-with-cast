# Wild Magics

## Overview
Component package under `monster/wild_magics` containing 4 files (`wild_fire_magic.lua`..`wild_water_magic.lua`).

## Interface
- `Game.createMonsterType("Wild Fire Magic")` and `mType:register(monster)` [wild_fire_magic.lua:Game.createMonsterType]
- `Game.createMonsterType("Wild Fury Magic")` and `mType:register(monster)` [wild_fury_magic.lua:Game.createMonsterType]
- `Game.createMonsterType("Wild Nature Magic")` and `mType:register(monster)` [wild_nature_magic.lua:Game.createMonsterType]
- `Game.createMonsterType("Wild Water Magic")` and `mType:register(monster)` [wild_water_magic.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [wild_fire_magic.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [wild_fury_magic.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [wild_nature_magic.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [wild_water_magic.lua:monster.flags]

## Side Effects
- Registers monster type `Wild Fire Magic` into the global `Game` engine registry via `mType:register(monster)` [wild_fire_magic.lua:mType:register]
- Registers monster type `Wild Fury Magic` into the global `Game` engine registry via `mType:register(monster)` [wild_fury_magic.lua:mType:register]
- Registers monster type `Wild Nature Magic` into the global `Game` engine registry via `mType:register(monster)` [wild_nature_magic.lua:mType:register]
- Registers monster type `Wild Water Magic` into the global `Game` engine registry via `mType:register(monster)` [wild_water_magic.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
