# KV Library (`src/kv`)

## Overview

The Canary KV Library (`src/kv`) provides a thread-safe, strongly-typed, persistent key-value store with an in-memory LRU cache (`KVStore`, capped at `MAX_SIZE = 1000000` entries), dot-prefixed hierarchical scopes (`ScopedKV`), variant value wrapping (`ValueWrapper`), Protobuf binary serialization (`ProtoSerializable`), and a SQL persistence backend (`KVSQL` writing to the `kv_store` table). It also underpins the Lua `kv` API and per-player scoped KV storage (`player->kv()`).

## Interface

- `[kv_definitions.hpp:ValueVariant]` — Variant type `std::variant<StringType, BooleanType, IntType, DoubleType, ArrayType, MapType>` representing supported KV values.
- `[value_wrapper.hpp:ValueWrapper]` — Timestamped wrapper around `ValueVariant` supporting typed extraction (`get<T>()`, `getNumber()`, `get(key)`, `get(index)`), tombstone marking (`deleted()`, `setDeleted(bool)`, `isDeleted()`), and implicit conversions.
- `[value_wrapper_proto.hpp:ProtoSerializable]` / `[value_wrapper_proto.hpp:ProtoHelpers]` — Converts between `ValueWrapper` and `Canary::protobuf::kv::ValueWrapper` (`toProto`, `fromProto`).
- `[kv.hpp:KV]` — Abstract KV interface (`set`, `get`, `remove`, `scoped`, `keys`, `saveAll`, `flush`, `generateUUID`).
- `[kv.hpp:KVStore]` / `[kv.hpp:g_kv]` — Thread-safe LRU-cached store base class (`MAX_SIZE = 1000000`, `getInstance()`, `set`, `get`, `flush`, `scoped`, `keys`) and global accessor `g_kv`.
- `[kv.hpp:ScopedKV]` — Dot-delimited prefix wrapper (`fmt::format("{}.{}", prefix_, key)`) delegating operations to a root `KVStore`.
- `[kv_sql.hpp:KVSQL]` — `final` SQL-backed `KVStore` implementation persisting Protobuf-serialized values to the `kv_store` database table (`saveAll()`, `load`, `save`, `loadPrefix`).

## Invariants

- `[kv.hpp:KVStore::MAX_SIZE]` / `[kv.cpp:KVStore::setLocked]` — In-memory `store_` never exceeds `MAX_SIZE` (`1,000,000`) entries; inserting a new key at capacity evicts the least-recently-used key from `lruQueue_.back()` into `pendingEvictions_`, which is persisted outside `mutex_` via `processEvictions()`.
- `[kv.cpp:KV::remove]` / `[kv.cpp:KVStore::get]` — Removing a key writes `ValueWrapper::deleted()` into the cache (`isDeleted() == true`), which causes `KVStore::get` (when `!forceLoad`) to move the entry to the back of `lruQueue_` and return `std::nullopt`, and causes `KVSQL::prepareSave` to execute a `DELETE FROM kv_store` query.
- `[kv.hpp:KV::generateUUID]` — Protected by `KV::mutex_`; generates strictly monotonic `<20-digit-ms>-<12-digit-counter>` strings by incrementing `counter_` when called multiple times within the same millisecond.
- `[value_wrapper.cpp:ValueWrapper::ValueWrapper]` — Whenever a `ValueWrapper` is constructed with `timestamp == 0`, `timestamp_` is initialized to `getTimeMsNow()`.

## Side Effects

- `[kv.cpp:KVStore::set]` / `[kv.cpp:KVStore::get]` / `[kv.hpp:KVStore::flush]` — Acquires `KVStore::mutex_`, mutates `store_`, `lruQueue_`, and `pendingEvictions_`, and invokes backend `load` / `save` outside the lock.
- `[kv_sql.cpp:KVSQL::load]` / `[kv_sql.cpp:KVSQL::loadPrefix]` — Executes synchronous `SELECT` queries against `kv_store` via `Database::storeQuery` and deserializes Protobuf payloads.
- `[kv_sql.cpp:KVSQL::save]` / `[kv_sql.cpp:KVSQL::saveAll]` — Serializes `ValueWrapper` instances via `ProtoSerializable::toProto` and executes `INSERT INTO kv_store ... ON DUPLICATE KEY UPDATE` (or `DELETE FROM kv_store` for deleted tombstones), wrapped in `DBTransaction::executeWithinTransaction` during `saveAll()`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`

---

## Features

- Thread-safe Operations: Multi-threaded environment friendly.
- Pluggable Backends: Support for various storage backends.
- Scoped Access: Organization-friendly scoped key-value pairs.
- LRU Caching: Cache management using LRU strategy.
- Strongly Typed: Type-safe value storage.
- Lua API Support: Manipulate KV store via Lua scripts.

## C++ API

### Initialization

```cpp
#include "kv/kv.hpp"

// In your class constructor
MyClass(KV &kv) : kv(kv) {}

// Or use the global singleton
KV &kv = g_kv();
```

### Basic Usage

```cpp
// Set an integer value
kv.set("age", 30);

// Get an integer value
int age = kv.get<int>("age");
```

### Scoped Access

```cpp
// Create a scoped KV store
auto scope = kv.scoped("raids");

// Set and get values in the scoped KV
scope->set("last-occurrence", getTimeNow());
int lastOccurrence = scope->get<int>("last-occurrence");
```

### Nested Scopes

```cpp
// Create a scoped KV store
auto scope = kv.scoped("raids")->scoped("raid-123");
scope->set("last-occurrence", getTimeNow());
int lastOccurrence = scope->get<int>("last-occurrence");
```

### Player Scope

```cpp
// Create a player-scoped KV store
auto player = g_game().getPlayerById(123);
auto playerKV = player->kv();
playerKV->set("coins", 100);
```

### Complex Types

```cpp
// arrays
kv.set("some-array", {1, 2, 3});
auto someArray = kv.get<ArrayType>("some-array");

// maps
kv.set("some-map", {{"a", 1}, {"b", 2}, {"c", 3}});
auto someMap = kv.get<MapType>("some-map");

// nested maps/arrays with non-uniform types
kv.set("some-nested", {{"a", {1, "string", 3}}, {"b", {"hehe", 5, 6}}});
auto someNested = kv.get<MapType>("some-nested");
```

## Lua API

### Error Handling

Errors are logged and return nil. Always check for nil when using kv.get().

### Basic Usage

```lua
-- Set and get an integer value
kv.set("age", 30)
local age = kv.get("age")
```

### Scoped Access

```lua
-- Create a scoped KV store
local scope = kv.scoped("raids")

-- Set and get values in the scoped KV
scope.set("last-occurrence", getTimeNow())
local lastOccurrence = scope:get("last-occurrence")
```

### Nested Scopes

```lua
-- Create a scoped KV store
local scope = kv.scoped("raids"):scoped("raid-123")
scope:set("last-occurrence", getTimeNow())
local lastOccurrence = scope:get("last-occurrence")
```

### Player Scope

```lua
-- Create a player-scoped KV store
local player = Player(123)
local playerKV = player:kv()
playerKV:set("coins", 100)
```

### Complex Types

```lua
-- arrays
kv.set("some-array", {1, 2, 3})
local someArray = kv.get("some-array")

-- maps
kv.set("some-map", {{"a", 1}, {"b", 2}, {"c", 3}})
local someMap = kv.get("some-map")

-- nested maps/arrays with non-uniform types
kv.set("some-nested", {{"a", {1, "string", 3}}, {"b", {"hehe", 5, 6}}})
local someNested = kv.get("some-nested")
```
