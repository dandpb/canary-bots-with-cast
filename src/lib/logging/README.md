# Logging (`src/lib/logging`)

## Overview

The `src/lib/logging` component defines Canary's logging abstraction (`Logger`) and its asynchronous `spdlog`-backed implementation (`LogWithSpdLog`). It provides formatted logging across severity levels (`trace`, `debug`, `info`, `warn`, `error`, `critical`), compile-time gating of `debug`/`trace` via `DEBUG_LOG`, and operation execution-time profiling to per-operation log files (`log/profile_log-<name>.txt`).

## Interface

- `[logger.hpp:Logger]` — Base logging interface providing `setLevel`, `getLevel`, `info`, `warn`, `error`, `critical`, `debug`, `trace`, `profile<Func>(name, func)`, and `logProfile(name, duration_ms)`.
- `[log_with_spd_log.hpp:LogWithSpdLog]` — `final` implementation of `Logger` backed by an asynchronous `spdlog` logger (`getInstance()`, `setLevel`, `getLevel`, `info`, `warn`, `error`, `critical`, `debug`, `trace`).
- `[log_with_spd_log.hpp:g_logger]` — Global `constexpr` accessor (`LogWithSpdLog::getInstance`) resolving `Logger&` via `inject<Logger>()`.

## Invariants

- `[logger.hpp:Logger]` — Non-copyable (`Logger(const Logger &) = delete` and `operator=(const Logger &) = delete`).
- `[logger.hpp:DEBUG_LOG]` / `[log_with_spd_log.hpp:DEBUG_LOG]` — `debug(...)` and `trace(...)` methods compile to no-ops unless the `DEBUG_LOG` preprocessor macro is defined.
- `[log_with_spd_log.cpp:LogWithSpdLog::LogWithSpdLog]` — Initializes the `spdlog` async thread pool with 8192 queue slots and 1 background worker thread (`spdlog::init_thread_pool(8192, 1)`), using `spdlog::async_overflow_policy::overrun_oldest`, default level `"info"`, flush on `warn`, and periodic flush every 3 seconds.

## Side Effects

- `[log_with_spd_log.cpp:LogWithSpdLog::LogWithSpdLog]` — Spawns a background `spdlog` thread pool, registers `"async_default"` (`stdout_color_sink_mt`) as the global default `spdlog` logger, and configures global `spdlog` pattern and flush policies.
- `[logger.cpp:Logger::setLevel]` / `[log_with_spd_log.cpp:LogWithSpdLog::setLevel]` — Mutates the global `spdlog` log level (`spdlog::set_level`).
- `[logger.cpp:Logger::logProfile]` — Sanitizes `:`, `\`, and `/` in the operation name to `_`, lazily creates a `spdlog::sinks::basic_file_sink_mt` writing to `log/profile_log-<name>.txt`, caches the logger in `profile_loggers_`, and writes profiling entries to disk.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
