# Core Support Libraries (`src/lib`)

## Overview

The `src/lib` directory is an intermediate blueprint grouping Canary's foundational infrastructure libraries: dependency injection (`di`), structured/async logging (`logging`), typed event/command messaging (`messaging`), OpenTelemetry metrics (`metrics`), and the worker thread pool (`thread`).

## Subdirectories & Boundaries

- [di](./di/README.md): Dependency injection container (`DI`, `inject<T>()`), `boost::di` runtime extensions, and `SoftSingleton` tracking.
- [logging](./logging/README.md): `Logger` interface, async `spdlog` implementation (`LogWithSpdLog`, `g_logger`), and per-operation file profiling.
- [messaging](./messaging/README.md): `eventpp`-backed `Message`, `ICommand` (`CommandType`), and `IEvent` (`EventType`) dispatchers and listeners.
- [metrics](./metrics/README.md): OpenTelemetry metrics (`metrics::Metrics`, `g_metrics`) and RAII latency histograms (`ScopedLatency`), gated by `FEATURE_METRICS`.
- [thread](./thread/README.md): `BS::thread_pool`-backed worker pool (`ThreadPool`, `g_threadPool`) and thread ID assignment.

## Interface

- `[di/container.hpp:DI]` / `[di/container.hpp:inject]` — Global dependency injection container and `inject<T>()` accessor.
- `[di/soft_singleton.hpp:SoftSingleton]` / `[di/soft_singleton.hpp:SoftSingletonGuard]` — Soft-singleton instance tracking and RAII guard.
- `[logging/logger.hpp:Logger]` / `[logging/log_with_spd_log.hpp:LogWithSpdLog]` / `[logging/log_with_spd_log.hpp:g_logger]` — Logging interface and async `spdlog` singleton.
- `[messaging/message.hpp:Message]` / `[messaging/command.hpp:CommandType]` / `[messaging/event.hpp:EventType]` — Typed message, command, and event dispatchers.
- `[metrics/metrics.hpp:metrics::Metrics]` / `[metrics/metrics.hpp:metrics::ScopedLatency]` / `[metrics/metrics.hpp:g_metrics]` — Metrics collection and scoped latency timers.
- `[thread/thread_pool.hpp:ThreadPool]` / `[thread/thread_pool.hpp:g_threadPool]` — Worker thread pool and task submission API.

## Invariants

- `[di/container.hpp:DI::get]` — `DI::get<T>()` and `inject<T>()` return shared singleton references from `testContainer` (if set) or `defaultContainer`.
- `[logging/logger.hpp:DEBUG_LOG]` — `debug` and `trace` logging compile to no-ops unless `DEBUG_LOG` is defined.
- `[metrics/metrics.hpp:FEATURE_METRICS]` — Metrics and latency scopes compile to no-ops unless `FEATURE_METRICS` is defined.
- `[thread/thread_pool.cpp:ThreadPool::ThreadPool]` — Ensures at least `DEFAULT_NUMBER_OF_THREADS` (4) worker threads when `threadCount == 0`.

## Side Effects

- `[logging/log_with_spd_log.cpp:LogWithSpdLog::LogWithSpdLog]` / `[logging/logger.cpp:Logger::logProfile]` — Initializes `spdlog` background threads, writes to stdout, and creates profile log files under `log/profile_log-*.txt`.
- `[metrics/metrics.cpp:Metrics::init]` — Initializes OpenTelemetry meter providers and Prometheus/OStream exporters when `FEATURE_METRICS` is enabled.
- `[thread/thread_pool.cpp:ThreadPool::shutdown]` — Transitions `g_game()` to `GAME_STATE_SHUTDOWN`, joins/resets worker threads, and restores default `SIGINT`/`SIGTERM` handlers.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
