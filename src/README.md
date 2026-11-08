# src

## Overview
Package implementation for `src`, providing component logic and data interfaces for src.

## Interface
- `lock` (`[canary_server.cpp:lock]`)
- `c_test` (`[canary_server.cpp:c_test]`)
- `config_lua_dist` (`[canary_server.cpp:config_lua_dist]`)
- `config_lua` (`[canary_server.cpp:config_lua]`)
- `FailedToInitializeCanary` (`[canary_server.cpp:FailedToInitializeCanary]`)
- `Logger` (`[canary_server.hpp:Logger]`)
- `FailedToInitializeCanary` (`[canary_server.hpp:FailedToInitializeCanary]`)
- `CanaryServer` (`[canary_server.hpp:CanaryServer]`)
- `LoaderStatus` (`[canary_server.hpp:LoaderStatus]`)
- `run` (`[canary_server.hpp:run]`)
- Subdirectory [`./account/README.md`](./account/README.md) - Sub-package for account
- Subdirectory [`./config/README.md`](./config/README.md) - Sub-package for config
- Subdirectory [`./creatures/README.md`](./creatures/README.md) - Sub-package for creatures
- Subdirectory [`./database/README.md`](./database/README.md) - Sub-package for database
- Subdirectory [`./enums/README.md`](./enums/README.md) - Sub-package for enums
- Subdirectory [`./game/README.md`](./game/README.md) - Sub-package for game
- Subdirectory [`./io/README.md`](./io/README.md) - Sub-package for io
- Subdirectory [`./items/README.md`](./items/README.md) - Sub-package for items
- Subdirectory [`./kv/README.md`](./kv/README.md) - Sub-package for kv
- Subdirectory [`./lib/README.md`](./lib/README.md) - Sub-package for lib
- Subdirectory [`./lua/README.md`](./lua/README.md) - Sub-package for lua
- Subdirectory [`./map/README.md`](./map/README.md) - Sub-package for map
- Subdirectory [`./protobuf/README.md`](./protobuf/README.md) - Sub-package for protobuf
- Subdirectory [`./security/README.md`](./security/README.md) - Sub-package for security
- Subdirectory [`./server/README.md`](./server/README.md) - Sub-package for server
- Subdirectory [`./utils/README.md`](./utils/README.md) - Sub-package for utils

## Invariants
- None

## Side Effects
- Executes SQL queries against game database (`[canary_server.cpp]`)
- Emits system diagnostic logs (`[canary_server.cpp]`)
- Schedules timed tasks or dispatcher callbacks (`[canary_server.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
