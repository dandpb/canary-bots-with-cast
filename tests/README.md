# test suites and QA fixtures

## Overview

C++ unit and integration tests use GoogleTest. Canary also has standalone Lua
regressions, in-server Lua acceptance tests and isolated Python/Docker fixtures.

### Lua script tests

Standalone Lua tests live in `tests/lua/` and need no build, server or database. Run them
from the repository root, e.g. `luajit tests/lua/test_bot_startup.lua` (or `lua5.4 ...`).
`test_bot_startup.lua` drives the real `BotStartup` handler with a fake dispatcher, clock
and DB: one pending load at a time, slicing and backoff on slow loads and late timers,
recovery, retries, quest access before hibernation, online visibility, the final
loaded/planned/failed count, stratified selection and end-of-load scheduling.

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

On Windows, the release test preset can also be used when validating the same build style used by the Windows release test configuration:

```powershell
cmake --preset windows-release-enabled-tests
cmake --build --preset windows-release-enabled-tests
.\build\windows-release-enabled-tests\tests\unit\canary_ut.exe
.\build\windows-release-enabled-tests\tests\integration\canary_it.exe
```

### Integration test database

Integration tests use the database configured by `tests/test.env` unless `TEST_ENV_FILE` points to another env file. The default database is `canary_test`, which is intended to be disposable.

When `TEST_DB_ALLOW_RESET=1`, the integration test executable checks schema sentinel columns before connecting. If a sentinel differs from the expected `schema.sql` shape, it drops and recreates the test database, then imports `schema.sql` using the `mysql` client. This reset is only allowed for database names that look like test databases.

Set `TEST_DB_SCHEMA` if the test executable cannot find `schema.sql` through the CMake-provided default path.

Persistent databases are updated through numbered Lua migrations under `data-otservbr-global/migrations`; the test reset path is only for disposable integration databases.

#### Direct executable access

You can also run test executables directly if needed:

```bash
./build/linux-debug/tests/unit/canary_ut
./build/linux-debug/tests/integration/canary_it
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

### GoogleTest

Tests are written using GoogleTest. Add new unit test files under `tests/unit` and register them in the nearest `CMakeLists.txt` with `target_sources`.

Basic test example:

```cpp
TEST(FooTest, DoesBar) {
	EXPECT_TRUE(true);
}
```

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
  cache + ccache) and runs `canary_ut` from the repository root. It runs on
  every pull request, push to `main` and manual dispatch.

In-server Lua acceptance and C++ integration tests are not part of CI; they
need the disposable database and game fixtures described above.
