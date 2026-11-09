# Lua Callbacks (`src/lua/callbacks`)

## Overview
Provides the event callback dispatch system for binding and executing Lua script hooks across creature, party, player, monster, zone, and map lifecycle events. It manages priority-ordered callback registration, duplication checks, argument marshalling onto the Lua stack, and in-place mutation of reference arguments such as `CombatDamage`.

## Interface
- `EventCallback_t` (`[callbacks_definitions.hpp:EventCallback_t]`): Enumeration of game events that trigger registered Lua callbacks.
- `CreatureCallback` (`[creaturecallback.hpp:CreatureCallback]`): Helper for invoking creature-targeted Lua callbacks (`startScriptInterface`, `pushSpecificCreature`, `persistLuaState`, `pushCreature`, `pushPosition`, `pushNumber`, `pushString`, `pushBoolean`).
- `EventCallback` (`[event_callback.hpp:EventCallback]`): Encapsulates a single named Lua event callback with enable/disable state, priority (`setPriority`/`getPriority`), script ID management (`loadScriptId`, `canExecute`), and variadic `execute(Args&&...)` dispatch.
- `EventCallbackManager` (`[event_callback_manager.hpp:EventCallbackManager]`): Priority-ordered per-event-type callback container supporting `registerCallback`, `unregisterCallback`, `checkCallback`, and `getCallbacks`.
- `EventsCallbacks` / `g_callbacks` (`[events_callbacks.hpp:EventsCallbacks]`, `[events_callbacks.hpp:g_callbacks]`): DI-backed singleton registry managing global event callbacks (`isCallbackRegistered`, `addCallback`, `clear`, `checkCallback`, `executeCallback`, `dispatchReturnValue`).

## Invariants
- `EventCallback` requires a non-null `LuaScriptInterface*` (defaulting to `g_scripts().getScriptInterface()`), asserted on construction (`[event_callback.cpp:EventCallback::EventCallback]`), and `canExecute()` requires `m_enabled == true`, `m_scriptId != kInvalidScriptId`, and a valid script interface (`[event_callback.cpp:EventCallback::canExecute]`).
- Callback priority is clamped to the range `[-1000, 1000]` (`[event_callback.hpp:EventCallback::setPriority]`), and `EventCallbackManager::registerCallback` maintains callbacks sorted in descending priority order (`[event_callback_manager.cpp:EventCallbackManager::registerCallback]`).
- Both `CreatureCallback::startScriptInterface` and `EventCallback::execute` must reserve a Lua script environment slot via `reserveScriptEnv()` before pushing functions or arguments (`[creaturecallback.cpp:CreatureCallback::startScriptInterface]`, `[event_callback.hpp:EventCallback::execute]`).
- Duplicate callback names for the same `EventCallback_t` are rejected unless `skipDuplicationCheck()` is true (`[event_callback_manager.cpp:EventCallbackManager::registerCallback]`, `[events_callbacks.cpp:EventsCallbacks::addCallback]`).

## Side Effects
- Reserves and mutates the global Lua `ScriptEnvironment` and `lua_State` stack, executing Lua functions and creating temporary `LUA_REGISTRYINDEX` references for `CombatDamage` tables (`[event_callback.hpp:EventCallback::execute]`, `[event_callback.hpp:EventCallback::pushDamageReference]`, `[creaturecallback.cpp:CreatureCallback::startScriptInterface]`).
- Mutates `CombatDamage` fields (`primary`, `secondary`, `origin`, `critical`) in-place from Lua table modifications after callback execution (`[event_callback.hpp:EventCallback::applyDamageReferences]`).
- Modifies in-memory callback registries in `EventsCallbacks::m_callbacks` and `EventCallbackManager::m_callbacks` (`[events_callbacks.cpp:EventsCallbacks::addCallback]`, `[event_callback_manager.cpp:EventCallbackManager::registerCallback]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
