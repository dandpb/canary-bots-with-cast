# lua

## Overview
Package implementation for `src/lua`, providing component logic and data interfaces for lua.

## Interface
- `LuaData_t` (`[lua_definitions.hpp:LuaData_t]`)
- `CreatureEventType_t` (`[lua_definitions.hpp:CreatureEventType_t]`)
- `MoveEvent_t` (`[lua_definitions.hpp:MoveEvent_t]`)
- `RaidState_t` (`[lua_definitions.hpp:RaidState_t]`)
- `TalkActionResult_t` (`[lua_definitions.hpp:TalkActionResult_t]`)
- `GlobalEvent_t` (`[lua_definitions.hpp:GlobalEvent_t]`)
- `ModuleType_t` (`[lua_definitions.hpp:ModuleType_t]`)
- `ErrorCode_t` (`[lua_definitions.hpp:ErrorCode_t]`)
- Subdirectory [`./callbacks/README.md`](./callbacks/README.md) - Sub-package for callbacks
- Subdirectory [`./creature/README.md`](./creature/README.md) - Sub-package for creature
- Subdirectory [`./functions/README.md`](./functions/README.md) - Sub-package for functions
- Subdirectory [`./global/README.md`](./global/README.md) - Sub-package for global
- Subdirectory [`./modules/README.md`](./modules/README.md) - Sub-package for modules
- Subdirectory [`./scripts/README.md`](./scripts/README.md) - Sub-package for scripts

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
