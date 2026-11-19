# C++ Integration Tests (`tests/integration`)

## Overview
Builds the `canary_it` GoogleTest executable, exercising real database transactions, account repositories, event callbacks, game mechanics, and `PlayerStorage` persistence.

## Interface
- `[CMakeLists.txt]` — Defines the `canary_it` test target and registers integration sources including `database_transaction_it.cpp`, `account/`, `event_callbacks/`, `game/`, and `player_storage/`.
- `[main.cpp]` / `[test_database.hpp]` / `[test_env.hpp]` — Integration test runner entrypoint and test database/environment helpers.
- `[database_transaction_it.cpp]` — Checks that a failed callback rolls back earlier statements and a second caller waits for the first transaction to finish.

## Invariants
- `canary_it` requires `CANARY_BUILD_TESTS=ON` and connects to MariaDB/MySQL at startup, including when running tests that inject a repository.
- Set `TEST_ENV_FILE` to an absolute path for the test connection settings. The build also looks for the repository's `tests/test.env` by default. Use a disposable database. Configure `TEST_DB_HOST`, `TEST_DB_PORT`, `TEST_DB_USER`, `TEST_DB_PASSWORD`, and `TEST_DB_NAME`. `TEST_DB_SOCKET` is optional. Environment variables override values from the file.

## Side Effects
- Connects to the configured test MySQL/MariaDB server and executes DDL/DML transactions during test execution.

## Verification
- After [building the tests](../README.md#running-tests) and configuring the test database, run `ctest --test-dir build/linux-debug/tests/integration --output-on-failure` from the repository root.
