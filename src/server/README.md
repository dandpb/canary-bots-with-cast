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
- Subdirectory [`./network/README.md`](./network/README.md) - Sub-package for network

## Invariants
- Validation assertion: `assert(!running)` (`[server.cpp]`)

## Side Effects
- Emits system diagnostic logs (`[server.cpp]`)
- Schedules timed tasks or dispatcher callbacks (`[server.cpp]`)
- Emits system diagnostic logs (`[server.hpp]`)
- Emits system diagnostic logs (`[signals.cpp]`)
- Schedules timed tasks or dispatcher callbacks (`[signals.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
