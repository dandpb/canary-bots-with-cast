# server

## Overview
Package implementation for `src/server`, providing component logic and data interfaces for server.

## Interface
- `Protocol` (`[server.hpp:Protocol]`)
- `ServiceBase` (`[server.hpp:ServiceBase]`)
- `Service` (`[server.hpp:Service]`)
- `ServicePort` (`[server.hpp:ServicePort]`)
- `ServiceManager` (`[server.hpp:ServiceManager]`)
- `openAcceptor` (`[server.hpp:openAcceptor]`)
- `open` (`[server.hpp:open]`)
- `close` (`[server.hpp:close]`)
- `HighscoreCharacter` (`[server_definitions.hpp:HighscoreCharacter]`)
- `ConnectionState_t` (`[server_definitions.hpp:ConnectionState_t]`)
- `Signals` (`[signals.hpp:Signals]`, `[signals.cpp:Signals::asyncWait]`, `[signals.cpp:Signals::dispatchSignalHandler]`): OS signal dispatcher for `SIGINT`, `SIGTERM`, `SIGHUP`, `SIGUSR1` (and `SIGBREAK` on Windows).
- Build target sources (`[CMakeLists.txt:target_sources]`): compiles `server.cpp`, `signals.cpp`, and `network/` including `network/protocol/visual_replay.cpp`.
- Subdirectory [`./network/README.md`](./network/README.md) - Sub-package for network

## Invariants
- Validation assertion: `assert(!running)` (`[server.cpp]`).
- `Signals::asyncWait` keeps listening across `GAME_STATE_SHUTDOWN`, and `Signals::dispatchSignalHandler` continues forwarding `SIGTERM` and `SIGINT` (plus `SIGBREAK` on Windows) during `GAME_STATE_SHUTDOWN` so operators can trigger a final-save retry after `SHUTDOWN_SAVE_FAILED` (`[signals.cpp:Signals::asyncWait]`, `[signals.cpp:Signals::dispatchSignalHandler]`).

## Side Effects
- Emits system diagnostic logs (`[server.cpp]`, `[server.hpp]`, `[signals.cpp]`).
- Schedules timed tasks or dispatcher callbacks (`[server.cpp]`, `[signals.cpp]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
