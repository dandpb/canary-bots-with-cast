# Hidden Threats

## Overview
Component package under `monster/quests/hidden_threats` containing 1 files (`cave_spider.lua`..`cave_spider.lua`).

## Interface
- `Game.createMonsterType("Cave Spider")` and `mType:register(monster)` [cave_spider.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cave_spider.lua:monster.flags]

## Side Effects
- Registers monster type `Cave Spider` into the global `Game` engine registry via `mType:register(monster)` [cave_spider.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
