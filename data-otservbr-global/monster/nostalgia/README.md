# Nostalgia

## Overview
Component package under `monster/nostalgia` containing 8 files (`old_bear.lua`..`old_wolf.lua`).

## Interface
- `Game.createMonsterType("Old Bear")` and `mType:register(monster)` [old_bear.lua:Game.createMonsterType]
- `Game.createMonsterType("Old Beholder")` and `mType:register(monster)` [old_bonelord.lua:Game.createMonsterType]
- `Game.createMonsterType("Old Bug")` and `mType:register(monster)` [old_bug.lua:Game.createMonsterType]
- `Game.createMonsterType("Old Giant Spider")` and `mType:register(monster)` [old_giant_spider.lua:Game.createMonsterType]
- `Game.createMonsterType("Old Pig")` and `mType:register(monster)` [old_pig.lua:Game.createMonsterType]
- `Game.createMonsterType("Old Spider")` and `mType:register(monster)` [old_spider.lua:Game.createMonsterType]
- `Game.createMonsterType("Old Wasp")` and `mType:register(monster)` [old_wasp.lua:Game.createMonsterType]
- `Game.createMonsterType("Old Wolf")` and `mType:register(monster)` [old_wolf.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [old_bear.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [old_bonelord.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [old_bug.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [old_giant_spider.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [old_pig.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [old_spider.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [old_wasp.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [old_wolf.lua:monster.flags]

## Side Effects
- Registers monster type `Old Bear` into the global `Game` engine registry via `mType:register(monster)` [old_bear.lua:mType:register]
- Registers monster type `Old Beholder` into the global `Game` engine registry via `mType:register(monster)` [old_bonelord.lua:mType:register]
- Registers monster type `Old Bug` into the global `Game` engine registry via `mType:register(monster)` [old_bug.lua:mType:register]
- Registers monster type `Old Giant Spider` into the global `Game` engine registry via `mType:register(monster)` [old_giant_spider.lua:mType:register]
- Registers monster type `Old Pig` into the global `Game` engine registry via `mType:register(monster)` [old_pig.lua:mType:register]
- Registers monster type `Old Spider` into the global `Game` engine registry via `mType:register(monster)` [old_spider.lua:mType:register]
- Registers monster type `Old Wasp` into the global `Game` engine registry via `mType:register(monster)` [old_wasp.lua:mType:register]
- Registers monster type `Old Wolf` into the global `Game` engine registry via `mType:register(monster)` [old_wolf.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
