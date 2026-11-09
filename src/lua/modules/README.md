# Lua Network Modules (`src/lua/modules`)

## Overview
Implements the XML-configured `Modules` subsystem (`modules.xml`), which binds custom client-to-server network packet opcodes (`recvbyte`) to Lua `onRecvbyte(player, msg, byte)` handlers with per-player rate-limiting delays.

## Interface
- `Module` (`[modules.hpp:Module]`): Represents a single packet-handling module inheriting from `Event` (`configureEvent`, `executeOnRecvbyte`, `clearEvent`, `copyEvent`, `getRecvbyte`, `getDelay`, `getEventType`, `isLoaded`).
- `Modules` / `g_modules` (`[modules.hpp:Modules]`, `[modules.hpp:g_modules]`): DI-managed singleton inheriting from `BaseEvents` that owns the `"Modules Interface"` Lua state and dispatches incoming opcodes (`executeOnRecvbyte`, `getEventByRecvbyte`).

## Invariants
- `Module::configureEvent` requires a `type="recvbyte"` XML attribute and a valid `byte` attribute; modules with `MODULE_TYPE_NONE` are rejected by `Modules::registerEvent` (`[modules.cpp:Module::configureEvent]`, `[modules.cpp:Modules::registerEvent]`).
- `Modules::executeOnRecvbyte` ignores module IDs equal to `0` and only executes a handler if `player->canRunModule(recvbyte)` returns true (`[modules.cpp:Modules::executeOnRecvbyte]`).
- `Module::executeOnRecvbyte` must reserve a script environment slot via `LuaScriptInterface::reserveScriptEnv()` before pushing the `Player` and weak `NetworkMessage` userdata onto the Lua stack (`[modules.cpp:Module::executeOnRecvbyte]`).

## Side Effects
- Initializes and resets its dedicated `LuaScriptInterface` (`"Modules Interface"`) and clears registered `Module` instances on `Modules::clear()` (`[modules.cpp:Modules::Modules]`, `[modules.cpp:Modules::clear]`).
- Updates per-player module cooldown timestamps via `player->setModuleDelay(recvbyte, delay)` and invokes Lua scripts that read from `NetworkMessage` (`[modules.cpp:Modules::executeOnRecvbyte]`, `[modules.cpp:Module::executeOnRecvbyte]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
