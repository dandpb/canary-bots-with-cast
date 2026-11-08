# events

## Overview
Package implementation for `src/lua/functions/events`, providing component logic and data interfaces for events.

## Interface
- `ActionFunctions` (`[action_functions.hpp:ActionFunctions]`)
- `init` (`[action_functions.hpp:init]`)
- `luaCreateAction` (`[action_functions.hpp:luaCreateAction]`)
- `luaActionOnUse` (`[action_functions.hpp:luaActionOnUse]`)
- `luaActionRegister` (`[action_functions.hpp:luaActionRegister]`)
- `luaActionItemId` (`[action_functions.hpp:luaActionItemId]`)
- `luaActionActionId` (`[action_functions.hpp:luaActionActionId]`)
- `luaActionUniqueId` (`[action_functions.hpp:luaActionUniqueId]`)
- `CreatureEventFunctions` (`[creature_event_functions.hpp:CreatureEventFunctions]`)
- `init` (`[creature_event_functions.hpp:init]`)

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[creature_event_functions.cpp]`)
- Emits system diagnostic logs (`[event_callback_functions.cpp]`)
- Emits system diagnostic logs (`[global_event_functions.cpp]`)
- Emits system diagnostic logs (`[move_event_functions.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
