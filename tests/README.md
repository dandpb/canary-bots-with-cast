# test suites and QA fixtures

## Overview

C++ unit and integration tests use GoogleTest. Canary also has standalone Lua
regressions, in-server Lua acceptance tests and isolated Python/Docker fixtures.

## Interface

- `[CMakeLists.txt]` enables the `canary_ut` and `canary_it` targets with
  `CANARY_BUILD_TESTS=ON` and registers GoogleTest cases with CTest.
- `unit/` covers C++ components such as player storage and the bot brain protocol.
- [C++ integration tests](integration/README.md) cover the database and game
  systems using a dedicated test database.
- [Lua regressions](lua/README.md) cover startup, progression and persistence.
- [Isolated QA fixtures](fixture/README.md) cover qualification, party scenarios
  and offline evidence processing.

## Running tests

From the repository root, configure and build a test-enabled preset. The
following example uses Linux. See `cmake --list-presets=all` for your platform.

```sh
cmake --preset linux-debug
cmake --build --preset linux-debug
ctest --test-dir build/linux-debug/tests/unit --output-on-failure
```

With a disposable database configured as described in the
[integration guide](integration/README.md), run the integration tests or the
complete CTest suite.

```sh
ctest --test-dir build/linux-debug/tests/integration --output-on-failure
ctest --preset linux-debug --output-on-failure
```

Use `ctest --preset linux-debug -N` to list discovered tests after building.
`ctest -R` filters by test name. For a manual build configured with `cmake -B build`,
use `ctest --test-dir build --output-on-failure` after enabling and building tests.

## Adding C++ tests

Place the file under the corresponding component in `tests/unit/` or
`tests/integration/` and add it to that directory's `CMakeLists.txt`. Use
GoogleTest's `TEST` or `TEST_F`. For existing examples, see
[bot brain protocol tests](unit/players/bot_brain_protocol_test.cpp) and
[database transaction tests](integration/database_transaction_it.cpp).

## Continuous integration

`.github/workflows/ci.yml` runs on pull requests, pushes to `main` and manual
dispatch:

- `lua` runs the standalone regressions ([Lua regressions](lua/README.md))
  under Lua 5.1 and LuaJIT.
- `python` installs `deployment/brain/requirements-dev.lock` plus the tracing
  extra, runs the brain suite from `deployment/brain`, the offline fixture
  suite (the ARM64-only persistence contract is skipped on AMD64 runners, see
  [isolated QA fixtures](fixture/README.md)), `ruff check`,
  `ruff format --check` and strict `mypy`. The source-metadata probe test
  needs cmake, Ninja, a C++ compiler and nlohmann-json; the workflow installs
  the headers and the runners provide the rest.
- `cpp` builds `canary`, `bot_engine` and `canary_ut` with the
  `linux-release-enabled-tests` preset on Ubuntu 22.04/GCC 13 (vcpkg binary
  cache + ccache) and runs `canary_ut` from the repository root. On pull
  requests it only runs when the diff touches `src/`, `cmake/`, `tests/unit/`,
  the CMake/vcpkg files or the workflows themselves; pushes and dispatch
  always run it.

In-server Lua acceptance and C++ integration tests are not part of CI; they
need the disposable database and game fixtures described above.
