# Lua Global Events & Base Types (`src/lua/global`)

## Overview
Defines foundational abstractions for XML/Lua event loading (`Event`, `BaseEvents`, `CallBack`), server-wide lifecycle and periodic timer events (`GlobalEvents`, `GlobalEvent`), shared-pointer self-casting (`SharedObject`), and core data structures for Lua timer descriptors (`LuaTimerEventDesc`) and variant values (`LuaVariant`).

## Interface
- `Event`, `BaseEvents`, `CallBack` (`[baseevents.hpp:Event]`, `[baseevents.hpp:BaseEvents]`, `[baseevents.hpp:CallBack]`): Base classes for XML-driven event systems (`loadFromXml`, `reload`, `reInitState`, `checkScript`, `loadScript`, `loadCallBack`).
- `GlobalEvents` / `g_globalEvents` & `GlobalEvent` (`[globalevent.hpp:GlobalEvents]`, `[globalevent.hpp:g_globalEvents]`, `[globalevent.hpp:GlobalEvent]`): Manages server startup, shutdown, save, light-period change, player record, interval (`think`), and time-of-day (`timer`) Lua events (`startup`, `shutdown`, `save`, `timer`, `think`, `execute`, `registerLuaEvent`, `clear`).
- `LuaTimerEventDesc` (`[lua_timer_event_descr.hpp:LuaTimerEventDesc]`): Move-enabled descriptor holding registry references (`function`, `parameters`), `scriptId`, `scriptName`, and `eventId` for scheduled `addEvent` Lua timers.
- `LuaVariant` (`[lua_variant.hpp:LuaVariant]`): Tagged union-like struct representing Lua combat/spell variant arguments (`type`, `text`, `instantName`, `runeName`, `pos`, `number`).
- `SharedObject` (`[shared_object.hpp:SharedObject]`): Base class inheriting `std::enable_shared_from_this<SharedObject>` with `static_self_cast` and `dynamic_self_cast` helper templates.

## Invariants
- `BaseEvents::loadFromXml` refuses to load if `loaded` is already true (`[baseevents.cpp:BaseEvents::loadFromXml]`).
- `Event::checkScript` validates candidate scripts in an isolated test Lua state (`g_luaEnvironment().getTestInterface()`) before `Event::loadScript` loads them into the target `LuaScriptInterface`, and requires `scriptId == 0` prior to loading (`[baseevents.cpp:Event::checkScript]`, `[baseevents.cpp:Event::loadScript]`).
- `GlobalEvents::registerLuaEvent` enforces unique event names within `timerMap`, `serverMap`, and `thinkMap` (`[globalevent.cpp:GlobalEvents::registerLuaEvent]`).
- `GlobalEvent` execution methods (`executePeriodChange`, `executeRecord`, `executeEvent`) must reserve a Lua script environment slot via `LuaScriptInterface::reserveScriptEnv()` (`[globalevent.cpp:GlobalEvent::executeEvent]`).

## Side Effects
- Schedules and stops recurring dispatcher tasks (`thinkEventId`, `timerEventId`) on `g_dispatcher()` (`[globalevent.cpp:GlobalEvents::registerLuaEvent]`, `[globalevent.cpp:GlobalEvents::timer]`, `[globalevent.cpp:GlobalEvents::think]`, `[globalevent.cpp:GlobalEvents::clear]`).
- Removes failed time-of-day events from `timerMap` if `globalEvent->executeEvent()` returns false, and advances `nextExecution` by 86400 seconds on success (`[globalevent.cpp:GlobalEvents::timer]`).
- Reads XML and Lua files from disk during `BaseEvents::loadFromXml` and reinitializes Lua states during `reload` and `checkScript` (`[baseevents.cpp:BaseEvents::loadFromXml]`, `[baseevents.cpp:Event::checkScript]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
