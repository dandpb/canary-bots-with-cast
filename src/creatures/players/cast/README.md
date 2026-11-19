# Cast Broadcaster Publisher (`src/creatures/players/cast`)

## Overview
Implements `CastPublisher` (`cast_publisher.hpp`, `cast_publisher.cpp`), keeping the `cast_broadcasters` database table synchronized with human `Player::setCastBroadcasting` transitions without blocking the game dispatcher thread or leaving stale rows on abrupt disconnects.

## Interface
- `CastPublisher`, `CastPublisher::Operation`, `CastPublisher::Executor`, `CastPublisher::Scheduler`, `g_castPublisher` (`[cast_publisher.hpp:CastPublisher]`, `[cast_publisher.hpp:CastPublisher::Operation]`, `[cast_publisher.hpp:g_castPublisher]`): Singleton per-GUID async publisher exposing `getInstance()`, `publish(guid, name)`, `unpublish(guid)`, `pendingCount()`, and `retryDelayMs(delayedRetries)`.
- Retry constants (`[cast_publisher.hpp:CastPublisher::kMaxAttempts]`, `[cast_publisher.hpp:CastPublisher::kRetryBaseDelayMs]`, `[cast_publisher.hpp:CastPublisher::kRetryMaxDelayMs]`): `kMaxAttempts = 3` immediate attempts followed by exponential timer backoff from `1000 ms` up to `60000 ms`.

## Invariants
- At most one SQL write (`UPSERT` or `DELETE`) per human player GUID is in flight at any time; concurrent requests coalesce by overwriting `Entry::desired` and incrementing `generation` so a stale `DELETE` can never overwrite a newer `publish` (`[cast_publisher.hpp:CastPublisher]`, `[cast_publisher.cpp:CastPublisher::request]`, `[cast_publisher.cpp:CastPublisher::onDone]`).
- Failed writes are never dropped while they remain the newest desired state: immediate retries run up to `kMaxAttempts` times, then scheduled backoff retries run until either persistence succeeds or a newer request supersedes the retry token (`[cast_publisher.cpp:CastPublisher::onDone]`, `[cast_publisher.cpp:CastPublisher::onRetry]`).
- Only human casters are routed through `CastPublisher`; native bots maintain their own `cast_broadcasters` persistence path inside `libbot_engine.so` (`[cast_publisher.hpp:CastPublisher]`).

## Side Effects
- Executes off-dispatcher SQL `INSERT ... ON DUPLICATE KEY UPDATE` and `DELETE` queries against `cast_broadcasters` on dedicated worker connections without acquiring the dispatcher database lock (`[cast_publisher.cpp:CastPublisher::getInstance]`).
- Schedules delayed backoff retry callbacks via `g_dispatcher()` when transient DB failures exhaust immediate retries (`[cast_publisher.cpp:CastPublisher::onDone]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
