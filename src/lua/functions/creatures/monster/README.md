# monster

## Overview
Package implementation for `src/lua/functions/creatures/monster`, providing component logic and data interfaces for monster.

## Interface
- `CharmFunctions` (`[charm_functions.hpp:CharmFunctions]`)
- `init` (`[charm_functions.hpp:init]`)
- `luaCharmCreate` (`[charm_functions.hpp:luaCharmCreate]`)
- `luaCharmName` (`[charm_functions.hpp:luaCharmName]`)
- `luaCharmDescription` (`[charm_functions.hpp:luaCharmDescription]`)
- `luaCharmCategory` (`[charm_functions.hpp:luaCharmCategory]`)
- `luaCharmType` (`[charm_functions.hpp:luaCharmType]`)
- `luaCharmPoints` (`[charm_functions.hpp:luaCharmPoints]`)
- `LootFunctions` (`[loot_functions.hpp:LootFunctions]`)
- `init` (`[loot_functions.hpp:init]`)

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[loot_functions.cpp]`)
- Emits system diagnostic logs (`[monster_functions.cpp]`)
- Emits system diagnostic logs (`[monster_spell_functions.cpp]`)
- Emits system diagnostic logs (`[monster_type_functions.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
