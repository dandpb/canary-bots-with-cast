# Metrics (`src/lib/metrics`)

## Overview

The `src/lib/metrics` component provides OpenTelemetry-based telemetry and latency instrumentation (`metrics::Metrics`, `metrics::ScopedLatency`, and category-specific RAII latency timers). When `FEATURE_METRICS` is disabled at compile time, all classes and methods compile to zero-overhead no-op stubs with identical interfaces.

## Interface

- `[metrics.hpp:metrics::Metrics]` — Telemetry manager singleton (`getInstance()`, `init(Options)`, `initHistograms()`, `shutdown()`, `addCounter(...)`, `addUpDownCounter(...)`).
- `[metrics.hpp:g_metrics]` — Global `constexpr` accessor (`metrics::Metrics::getInstance`) resolving `metrics::Metrics&` via `inject<Metrics>()`.
- `[metrics.hpp:metrics::Options]` / `[metrics.hpp:Options]` — Exporter configuration (`enablePrometheusExporter`, `enableOStreamExporter`, plus OpenTelemetry reader/exporter options when `FEATURE_METRICS` is enabled).
- `[metrics.hpp:metrics::ScopedLatency]` / `[metrics.hpp:ScopedLatency]` — RAII timer measuring elapsed microseconds on `std::chrono::steady_clock` and recording to an OpenTelemetry histogram on `stop()` or destruction.
- `[metrics.hpp:metrics::method_latency]` / `[metrics.hpp:metrics::lua_latency]` / `[metrics.hpp:metrics::query_latency]` / `[metrics.hpp:metrics::task_latency]` / `[metrics.hpp:metrics::lock_latency]` — Category-specific `ScopedLatency` subclasses generated via `DEFINE_LATENCY_CLASS` for `latencyNames` (`method_latency`, `lua_latency`, `query_latency`, `task_latency`, `lock_latency`).

## Invariants

- `[metrics.hpp:FEATURE_METRICS]` — When `FEATURE_METRICS` is not defined, `Metrics` and `ScopedLatency` methods are compile-time no-ops.
- `[metrics.cpp:ScopedLatency::stop]` — Idempotent: guarded by `if (stopped) return;`, ensuring each `ScopedLatency` instance records at most one observation.
- `[metrics.hpp:metrics::Metrics::addCounter]` / `[metrics.hpp:metrics::Metrics::addUpDownCounter]` — Protected by `std::scoped_lock lock(mutex_)` and no-ops if `getMeter()` returns null.

## Side Effects

- `[metrics.cpp:Metrics::init]` — Creates an OpenTelemetry `MeterProvider`, optionally attaches `OStreamMetricExporter` and/or `PrometheusExporter` (starting an HTTP endpoint at `opts.prometheusOptions.url`), sets the global `Provider::SetMeterProvider`, and registers histogram views in `initHistograms()`.
- `[metrics.cpp:Metrics::shutdown]` — Resets the global OpenTelemetry `MeterProvider` to an empty `shared_ptr`.
- `[metrics.cpp:ScopedLatency::stop]` — Records elapsed microseconds (`elapsed`) into the target OpenTelemetry `Histogram<double>`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
