# Core Lua Functions

## Overview
Top-level coordinator for core Lua bindings in the server scripting environment. `CoreFunctions` aggregates and initializes the `game`, `libs`, and `network` Lua binding sub-packages into a `lua_State*`.

## Interface
- `CoreFunctions` (`[core_functions.hpp:CoreFunctions]`) — `LuaScriptInterface` final class that delegates initialization to `CoreGameFunctions::init(L)`, `CoreLibsFunctions::init(L)`, and `CoreNetworkFunctions::init(L)` via `CoreFunctions::init(lua_State* L)` (`[core_functions.hpp:CoreFunctions::init]`).
- [game](./game/README.md): Core game state, `Game`, `Bank`, `configManager`, `ModalWindow`, `Zone`, global functions, and enums.
- [libs](./libs/README.md): Core infrastructure libraries (`db`, `Result`, `kv`/`KV`, `logger`/`Spdlog`, `metrics`).
- [network](./network/README.md): Network packet manipulation (`NetworkMessage`) and webhook dispatch (`Webhook`).

## Invariants
- Expects a valid, non-null `lua_State* L` initialized by `Lua::load` (`[core_functions.hpp:CoreFunctions::init]`).

## Side Effects
- Populates the Lua global environment with all core game, library, and network tables, classes, metatables, and constants (`[core_functions.hpp:CoreFunctions::init]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
