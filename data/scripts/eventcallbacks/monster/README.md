# monster

## Overview
Package implementation for `data/scripts/eventcallbacks/monster`, providing component logic and data interfaces for monster.

## Interface
- `callback.monsterOnDropLoot` (`[ondroploot__base.lua:callback.monsterOnDropLoot]`)
- `callback.monsterOnDropLoot` (`[ondroploot_boosted.lua:callback.monsterOnDropLoot]`)
- `callback.monsterOnDropLoot` (`[ondroploot_gem_atelier.lua:callback.monsterOnDropLoot]`)
- `callback.monsterOnDropLoot` (`[ondroploot_hazard.lua:callback.monsterOnDropLoot]`)
- `callback.monsterOnDropLoot` (`[ondroploot_prey.lua:callback.monsterOnDropLoot]`)
- `callback.monsterOnDropLoot` (`[ondroploot_wealth_duplex.lua:callback.monsterOnDropLoot]`)
- `callback.monsterPostDropLoot` (`[postdroploot_analyzer.lua:callback.monsterPostDropLoot]`)

## Invariants
- None

## Side Effects
- None

## Verification
- See the [Lua regression guide](../../../../tests/lua/README.md).
