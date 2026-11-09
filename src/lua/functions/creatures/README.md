# creatures

## Overview
Package implementation for `src/lua/functions/creatures`, providing component logic and data interfaces for creatures.

## Interface
- `CreatureFunctions` (`[creature_functions.hpp:CreatureFunctions]`)
- `init` (`[creature_functions.hpp:init]`)
- `luaCreatureCreate` (`[creature_functions.hpp:luaCreatureCreate]`)
- `luaCreatureGetEvents` (`[creature_functions.hpp:luaCreatureGetEvents]`)
- `luaCreatureRegisterEvent` (`[creature_functions.hpp:luaCreatureRegisterEvent]`)
- `luaCreatureUnregisterEvent` (`[creature_functions.hpp:luaCreatureUnregisterEvent]`)
- `luaCreatureIsRemoved` (`[creature_functions.hpp:luaCreatureIsRemoved]`)
- `luaCreatureIsCreature` (`[creature_functions.hpp:luaCreatureIsCreature]`)
- Subdirectory [`./combat/README.md`](./combat/README.md) - Sub-package for combat
- Subdirectory [`./monster/README.md`](./monster/README.md) - Sub-package for monster
- Subdirectory [`./npc/README.md`](./npc/README.md) - Sub-package for npc
- Subdirectory [`./player/README.md`](./player/README.md) - Sub-package for player

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[creature_functions.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
