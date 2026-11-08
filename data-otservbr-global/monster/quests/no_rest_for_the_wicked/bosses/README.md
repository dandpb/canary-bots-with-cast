# Bosses

## Overview
Component package under `monster/quests/no_rest_for_the_wicked/bosses` containing 1 files (`arbaziloth.lua`..`arbaziloth.lua`).

## Interface
- `Game.createMonsterType("Arbaziloth")` and `mType:register(monster)` [arbaziloth.lua:Game.createMonsterType]
- `mType.onAppear` lifecycle callback [arbaziloth.lua:mType.onAppear]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [arbaziloth.lua:monster.flags]

## Side Effects
- Registers monster type `Arbaziloth` into the global `Game` engine registry via `mType:register(monster)` [arbaziloth.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
