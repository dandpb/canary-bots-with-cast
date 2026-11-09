# functions

## Overview
Package implementation for `src/lua/functions`, providing component logic and data interfaces for functions.

## Interface
- `LuaScriptInterface` (`[lua_functions_loader.cpp:LuaScriptInterface]`)
- `luaL_ref` (`[lua_functions_loader.cpp:luaL_ref]`)
- `getString` (`[lua_functions_loader.cpp:getString]`)
- `Combat` (`[lua_functions_loader.hpp:Combat]`)
- `Creature` (`[lua_functions_loader.hpp:Creature]`)
- `Cylinder` (`[lua_functions_loader.hpp:Cylinder]`)
- `Game` (`[lua_functions_loader.hpp:Game]`)
- `InstantSpell` (`[lua_functions_loader.hpp:InstantSpell]`)
- `Item` (`[lua_functions_loader.hpp:Item]`)
- `Player` (`[lua_functions_loader.hpp:Player]`)
- Subdirectory [`./core/README.md`](./core/README.md) - Sub-package for core
- Subdirectory [`./creatures/README.md`](./creatures/README.md) - Sub-package for creatures
- Subdirectory [`./events/README.md`](./events/README.md) - Sub-package for events
- Subdirectory [`./items/README.md`](./items/README.md) - Sub-package for items
- Subdirectory [`./map/README.md`](./map/README.md) - Sub-package for map

## Invariants
- Validation assertion: `assert(interface)` (`[lua_functions_loader.cpp]`)
- Validation assertion: `assert(scriptEnvIndex >= 0 && scriptEnvIndex < 16)` (`[lua_functions_loader.hpp]`)
- Validation assertion: `assert(scriptEnvIndex >= 0)` (`[lua_functions_loader.hpp]`)

## Side Effects
- Emits system diagnostic logs (`[lua_functions_loader.cpp]`)
- Schedules timed tasks or dispatcher callbacks (`[lua_functions_loader.cpp]`)
- Emits system diagnostic logs (`[lua_functions_loader.hpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
