# Core Libraries Lua Functions

## Overview
Provides Lua bindings for core server infrastructure libraries: relational database access (`db` and `Result`), hierarchical key-value storage (`kv` and `KV`), structured logging (`logger` and legacy `Spdlog`), and telemetry counters (`metrics`).

## Interface
- `CoreLibsFunctions` (`[core_libs_functions.hpp:CoreLibsFunctions]`) — Aggregator `LuaScriptInterface` subclass that initializes all core library Lua bindings via `CoreLibsFunctions::init(lua_State* L)` (`[core_libs_functions.hpp:CoreLibsFunctions::init]`).
- `DBFunctions` (`[db_functions.hpp:DBFunctions]`) — Registers the `db` table (`query`, `asyncQuery`, `storeQuery`, `asyncStoreQuery`, `botAsyncQuery`, `botAsyncStoreQuery`, `escapeString`, `escapeBlob`, `lastInsertId`, `tableExists`) via `DBFunctions::init(lua_State* L)` (`[db_functions.cpp:DBFunctions::init]`).
- `ResultFunctions` (`[result_functions.hpp:ResultFunctions]`) — Registers the `Result` table (`getNumber`, `getString`, `getStream`, `next`, `free`) for iterating and releasing stored query results via `ResultFunctions::init(lua_State* L)` (`[result_functions.cpp:ResultFunctions::init]`).
- `KVFunctions` (`[kv_functions.hpp:KVFunctions]`) — Registers the `kv` table and `KV` class (`scoped`, `set`, `get`, `keys`, `remove`) for reading and writing `ValueWrapper` values via `KVFunctions::init(lua_State* L)` (`[kv_functions.cpp:KVFunctions::init]`).
- `LoggerFunctions` (`[logger_functions.hpp:LoggerFunctions]`) — Registers the `logger` table (`info`, `warn`, `error`, `debug`, `trace`) and deprecated `Spdlog` table via `LoggerFunctions::init(lua_State* L)` (`[logger_functions.cpp:LoggerFunctions::init]`).
- `MetricsFunctions` (`[metrics_functions.hpp:MetricsFunctions]`) — Registers the `metrics` table (`addCounter`) via `MetricsFunctions::init(lua_State* L)` (`[metrics_functions.cpp:MetricsFunctions::init]`).

## Invariants
- Asynchronous database callbacks (`asyncQuery`, `asyncStoreQuery`, `botAsyncQuery`, `botAsyncStoreQuery`) store the Lua callback in `LUA_REGISTRYINDEX`, require `Lua::reserveScriptEnv()` before invoking `g_luaEnvironment().callFunction(1)`, and always unref the registry entry (`[db_functions.cpp:DBFunctions::luaDatabaseAsyncExecute]`, `[db_functions.cpp:DBFunctions::luaDatabaseBotAsyncStoreQuery]`).
- `ResultFunctions` methods look up active result handles via `ScriptEnvironment::getResultByID` and require explicit release via `Result.free` (`ScriptEnvironment::removeResult`) (`[result_functions.cpp:ResultFunctions::luaResultGetNumber]`, `[result_functions.cpp:ResultFunctions::luaResultFree]`).
- `KVFunctions::getValueWrapper` only accepts boolean, number, string, array tables, or string-keyed map tables; `nil` or unsupported types return `std::nullopt` and log a warning (`[kv_functions.cpp:KVFunctions::getValueWrapper]`).

## Side Effects
- Executes synchronous SQL queries directly on `Database::getInstance()` and dispatches asynchronous SQL queries to `g_databaseTasks()` or the dedicated bot worker `g_botDatabaseTasks()` (`[db_functions.cpp:DBFunctions::luaDatabaseExecute]`, `[db_functions.cpp:DBFunctions::luaDatabaseAsyncExecute]`, `[db_functions.cpp:DBFunctions::luaDatabaseBotAsyncExecute]`).
- Mutates `ScriptEnvironment` result maps when storing or freeing `DBResult_ptr` handles (`[db_functions.cpp:DBFunctions::luaDatabaseStoreQuery]`, `[result_functions.cpp:ResultFunctions::luaResultFree]`).
- Mutates in-memory/persistent key-value state via `g_kv()` and `KV` scopes (`[kv_functions.cpp:KVFunctions::luaKVSet]`, `[kv_functions.cpp:KVFunctions::luaKVRemove]`).
- Emits formatted log entries to `g_logger()` and counter increments to `g_metrics()` (`[logger_functions.cpp:LoggerFunctions::luaLoggerInfo]`, `[metrics_functions.cpp:MetricsFunctions::luaMetricsAddCounter]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
