# Task Scheduling & Save Management (`src/game/scheduling`)

## Overview
Provides the central asynchronous task loop (`Dispatcher` and `Task`), calendar-driven event rate scheduling (`EventsScheduler`), and durable persistence orchestration (`SaveManager` and `SerialSaveQueue`) for players, bots, guilds, map state, and the key-value store.

## Interface
- `Dispatcher` / `g_dispatcher`, `DispatcherContext`, `TaskGroup`, `DispatcherType` (`[dispatcher.hpp:Dispatcher]`, `[dispatcher.hpp:g_dispatcher]`, `[dispatcher.hpp:DispatcherContext]`, `[dispatcher.hpp:TaskGroup]`, `[dispatcher.hpp:DispatcherType]`): Main game event loop and parallel task coordinator (`addEvent`, `addWalkEvent`, `cycleEvent`, `scheduleEvent`, `asyncEvent`, `asyncWait`, `asyncCycleEvent`, `asyncScheduleEvent`, `safeCall`, `stopEvent`, `isOnDispatcherThread`, `isShuttingDown`).
- `Task` (`[task.hpp:Task]`): Callable unit of work with expiration, delay, cycle flag, and monotonic event ID (`getId`, `getDelay`, `getContext`, `getTime`, `hasExpired`, `isCycle`, `isCanceled`, `cancel`, `execute`).
- `EventsScheduler` / `g_eventsScheduler`, `EventScheduler`, `EventRates` (`[events_scheduler.hpp:EventsScheduler]`, `[events_scheduler.hpp:g_eventsScheduler]`, `[events_scheduler.hpp:EventScheduler]`, `[events_scheduler.hpp:EventRates]`): JSON/XML calendar event loader and rate multiplier manager (`loadScheduleEventFromJson`, `loadScheduleEventFromXml`, `getExpSchedule`, `getLootSchedule`, `getBossLootSchedule`, `getSpawnMonsterSchedule`, `getSkillSchedule`, `getActiveEvents`, `reset`).
- `SaveManager` / `g_saveManager` (`[save_manager.hpp:SaveManager]`, `[save_manager.hpp:g_saveManager]`): Coordinates full server saves and individual player/bot/guild saves (`saveAll`, `scheduleAll`, `savePlayer`, `saveBotPosition`, `getPendingBotPlayer`, `saveGuild`).
- `SerialSaveQueue<Value>` (`[serial_save_queue.hpp:SerialSaveQueue]`): Thread-safe, generation-tracked per-GUID save coalescing queue (`request`, `take`, `finish`, `find`, `snapshot`).

## Invariants
- `Dispatcher` pre-allocates `threadPool.get_thread_count() + 4` `ThreadTask` slots so every thread calling `ThreadPool::getThreadId()` (pool workers, main/asio thread, `BotDatabaseTasks` worker) indexes `threads` in-bounds without locking a global queue (`[dispatcher.hpp:Dispatcher::Dispatcher]`, `[dispatcher.hpp:Dispatcher::getThreadTask]`).
- Once `Dispatcher::shutdown()` sets `shuttingDown = true`, all new enqueue calls (`addEvent`, `addWalkEvent`, `scheduleEvent`, `asyncEvent`) are dropped and `executeScheduledEvents()` immediately returns so `[this]`-capturing lambdas cannot fire on destroyed map/spawn objects (`[dispatcher.hpp:Dispatcher::shutdown]`, `[dispatcher.cpp:Dispatcher::executeScheduledEvents]`).
- `Dispatcher::asyncWait` sets `asyncWaitDisabled = true` while a parallel partition is active to prevent nested `asyncWait` fork-join deadlocks (`[dispatcher.cpp:Dispatcher::asyncWait]`).
- `Task` constructors assert that `context` is non-empty (`!this->context.empty()`), and `Task::getId()` generates non-zero monotonic IDs skipping `0` on wrap-around (`[task.hpp:Task::getId]`, `[task.cpp:Task::Task]`).
- `SerialSaveQueue::finish` compares the completed `generation` against `entry.generation`: if a newer generation was requested while the worker was running, it returns `true` so the worker immediately persists the newer state, and on failure (`success == false`) retains the entry in `entries_` (`[serial_save_queue.hpp:SerialSaveQueue::finish]`).
- `SaveManager::captureBatch` and `SaveManager::enqueueBot` capture `PlayerSaveSnapshot` checkpoints on the dispatcher thread before handing off SQL execution to the dedicated 4-thread `botSavePool_`, ensuring worker threads never touch mutable `Player` state or the unloadable bot engine (`[save_manager.hpp:SaveManager::botSavePool_]`, `[save_manager.cpp:SaveManager::captureBatch]`, `[save_manager.cpp:SaveManager::enqueueBot]`).

## Side Effects
- Spawns the detached main dispatcher loop on `threadPool`, updates `OTSYS_TIME()` each cycle, drains `DbDispatcherStats::fetchResetSyncDbUs()`, and logs jitter telemetry (`[CYCLE_SLOW]`, `[CYCLE_GAP]`, `[DISP_SLOW]`, `[ASYNC_WAIT]`, `[DISP_RATES]`) (`[dispatcher.cpp:Dispatcher::init]`, `[dispatcher.cpp:Dispatcher::executeSerialEvents]`, `[dispatcher.cpp:Dispatcher::executeScheduledEvents]`).
- `SaveManager::runBotSave` opens thread-local `Database` connections on `botSavePool_` workers, executes SQL transactions (`IOLoginData::persistPlayerSave` or `UPDATE players`), and posts `IOLoginData::acknowledgePlayerSave` back to `g_dispatcher()` (`[save_manager.cpp:SaveManager::runBotSave]`).
- `SaveManager` persists players, guilds, map state (`Map::save`), and key-value entries (`kv.saveAll()`) (`[save_manager.cpp:SaveManager::saveBatch]`, `[save_manager.cpp:SaveManager::doSavePlayer]`).
- `EventsScheduler` reads `events.json` / `events.xml`, loads event Lua scripts via `g_scripts().loadEventSchedulerScripts`, mutates global schedule rate multipliers and `g_kv().scoped("eventscheduler")` keys (`forge-chance`, `double-bestiary`, `double-bosstiary`, `fast-exercise`, `boss-cooldown`), and calls `consoleHandlerExit()` on missing/corrupt schedule files (`[events_scheduler.cpp:EventsScheduler::loadScheduleEventFromJson]`, `[events_scheduler.cpp:EventsScheduler::loadScheduleEventFromXml]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
