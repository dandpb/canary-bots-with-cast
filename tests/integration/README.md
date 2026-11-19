# C++ Integration Tests (`tests/integration`)

## Overview
Builds the `canary_it` integration test executable using `Boost::ut`, exercising real database transactions, account repositories, event callbacks, game mechanics, and `PlayerStorage` persistence.

## Interface
- `[CMakeLists.txt]` — Defines the `canary_it` test target and registers integration sources including `database_transaction_it.cpp`, `account/`, `event_callbacks/`, `game/`, and `player_storage/`.
- `[main.cpp]` / `[test_database.hpp]` / `[test_env.hpp]` — Integration test runner entrypoint and test database/environment helpers.
- `[database_transaction_it.cpp]` — Integration test verifying `Database` / `DBTransaction` commit, rollback, and uncertain transaction outcome semantics.

## Invariants
- `canary_it` requires `CANARY_BUILD_TESTS=ON` and uses isolated test database configuration provided via `test_env.hpp` / `test_database.hpp`.

## Side Effects
- Connects to the configured test MySQL/MariaDB server and executes DDL/DML transactions during test execution.

## Verification
- Run: `ctest --preset linux-debug -R integration --output-on-failure`
