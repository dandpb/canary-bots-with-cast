# Lua Script Engine & Environments (`src/lua/scripts`)

## Overview
Provides the core LuaJIT state lifecycle, script execution interface, call-stack environment tracking, and recursive directory script loader (`revscriptsys`). It manages the primary `lua_State`, event registry tables, temporary script-scoped items and DB results, `AreaCombat` ownership, and `addEvent` timer execution.

## Interface
- `LuaEnvironment` / `g_luaEnvironment` (`[lua_environment.hpp:LuaEnvironment]`, `[lua_environment.hpp:g_luaEnvironment]`): Main Lua state singleton (`getLuaState`, `initState`, `reInitState`, `closeState`, `getTestInterface`, `getAreaObject`, `createAreaObject`, `clearAreaObjects`, `collectGarbage`, `isShuttingDown`).
- `LuaScriptInterface` (`[luascript.hpp:LuaScriptInterface]`): Script compilation and invocation wrapper inheriting `Lua` (`initState`, `reInitState`, `loadFile`, `getEvent`, `getMetaEvent`, `getFileById`, `pushFunction`, `callFunction`, `callVoidFunction`, `getStackTrace`).
- `ScriptEnvironment` (`[script_environment.hpp:ScriptEnvironment]`): Per-call frame environment tracking active `scriptId`, `LuaScriptInterface*`, `Npc`, local item UIDs, temporary items, and DB query results (`resetEnv`, `setScriptId`, `setCallbackId`, `addThing`, `getThingByUID`, `addTempItem`, `removeTempItem`, `addResult`, `removeResult`, `getResultByID`).
- `Scripts` / `g_scripts` (`[scripts.hpp:Scripts]`, `[scripts.hpp:g_scripts]`): Recursive `.lua` script loader and subsystem cleaner (`loadScripts`, `loadEventSchedulerScripts`, `clearAllScripts`, `getScriptInterface`).
- `luaL_register` / `lua_equal` (`[luajit_sync.hpp:luaL_register]`, `[luajit_sync.hpp:lua_equal]`): Lua 5.2+ compatibility macros for LuaJIT synchronization.

## Invariants
- `Lua::scriptEnv` has a fixed recursion depth of 16 frames (`[luascript.cpp:Lua::scriptEnv]`); every script load or callback execution must pair `reserveScriptEnv()` with `resetScriptEnv()`, and `LuaScriptInterface::callFunction`/`callVoidFunction` verify that the Lua stack top is restored after `protectedCall` (`[luascript.cpp:LuaScriptInterface::callFunction]`, `[luascript.cpp:LuaScriptInterface::callVoidFunction]`).
- `ScriptEnvironment::setCallbackId` forbids nested callbacks within the same environment frame (`this->callbackId != 0`) (`[script_environment.cpp:ScriptEnvironment::setCallbackId]`).
- `ScriptEnvironment::getThingByUID` partitions UID space: UIDs `>= 0x10000000` resolve to creatures via `g_game().getCreatureByID`, UIDs `<= 0xFFFF` resolve to global unique items via `g_game().getUniqueItem`, and UIDs `> 0xFFFF` resolve to script-local items in `localMap` (`[script_environment.cpp:ScriptEnvironment::getThingByUID]`).
- `Scripts::loadScripts` skips any `.lua` file whose filename starts with `#`, and when `isLib == false` skips files whose immediate parent directory is `"lib"` or `"events"` (`[scripts.cpp:Scripts::loadScripts]`).
- `LuaEnvironment::collectGarbage` guards against recursive invocations with a static `collecting` flag and runs `lua_gc(luaState, LUA_GCCOLLECT, 0)` twice so uservalue `__gc` metamethods execute (`[lua_environment.cpp:LuaEnvironment::collectGarbage]`).

## Side Effects
- Allocates, mutates, and closes the global `lua_State` (`luaL_newstate`, `lua_close`), registers all C++ Lua bindings via `Lua::load(luaState)`, and manages `LUA_REGISTRYINDEX` references for event tables and timer parameters (`[lua_environment.cpp:LuaEnvironment::initState]`, `[lua_environment.cpp:LuaEnvironment::closeState]`, `[luascript.cpp:LuaScriptInterface::initState]`).
- `Scripts::clearAllScripts` clears registered state across `g_actions()`, `g_creatureEvents()`, `g_talkActions()`, `g_globalEvents()`, `g_spells()`, `g_moveEvents()`, `g_weapons()`, `g_callbacks()`, and `g_monsters()` (`[scripts.cpp:Scripts::clearAllScripts]`).
- Reads and executes `.lua` files from the filesystem during `Scripts::loadScripts` and `Scripts::loadEventSchedulerScripts` (`[scripts.cpp:Scripts::loadScripts]`, `[scripts.cpp:Scripts::loadEventSchedulerScripts]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
