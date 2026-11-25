# creature

## Overview
Package implementation for `data/scripts/eventcallbacks/creature`, providing component logic and data interfaces for creature.

## Interface
- `callback.creatureOnAreaCombat` (`[on_area_combat.lua:callback.creatureOnAreaCombat]`)
- `callback.creatureOnCombat` (`[on_combat_taskboard.lua:callback.creatureOnCombat]`): Applies `Taskboard.getDamageBonus` and `Taskboard.getLifeLeechBonus` when a player damages a monster while `Taskboard.isEnabled()` is true.

## Invariants
- None

## Side Effects
- None

## Verification
- See the [Lua regression guide](../../../../tests/lua/README.md).
