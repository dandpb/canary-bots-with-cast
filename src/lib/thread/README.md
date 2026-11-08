# Thread Pool (`src/lib/thread`)

## Overview

The `src/lib/thread` component provides Canary's centralized multi-threaded task execution pool (`ThreadPool`), backed by `BS::thread_pool`. It supports detached task submission, future-returning task and loop submission, thread-local sequential thread ID assignment (`getThreadId()`), and coordinated shutdown with the game state.

## Interface

- `[thread_pool.hpp:ThreadPool]` — Thread pool wrapper (`getInstance()`, `detach_task(F&&)`, `submit_loop(first, last, F&&)`, `submit_task(F&&, Args&&...)`, `wait_for_tasks()`, `get_thread_count()`, `start()`, `shutdown()`, `getThreadId()`, `isStopped()`).
- `[thread_pool.hpp:g_threadPool]` — Global `constexpr` accessor (`ThreadPool::getInstance`) resolving `ThreadPool&` via `inject<ThreadPool>()`.
- `[thread_pool.cpp:DEFAULT_NUMBER_OF_THREADS]` — Fallback minimum thread count (`4`) when `threadCount == 0` and hardware concurrency is lower.

## Invariants

- `[thread_pool.hpp:ThreadPool]` — Non-copyable (`ThreadPool(const ThreadPool &) = delete` and `operator=(const ThreadPool &) = delete`).
- `[thread_pool.cpp:ThreadPool::ThreadPool]` — Pool size is `threadCount` when `threadCount > 0`, otherwise `std::max<int>(getNumberOfCores(), DEFAULT_NUMBER_OF_THREADS)` (at least 4 threads).
- `[thread_pool.hpp:ThreadPool::getThreadId]` — Assigns each calling thread a unique, monotonically increasing `int16_t` ID starting at `0` using `static std::atomic_int16_t lastId` and `thread_local static int16_t id`.
- `[thread_pool.cpp:ThreadPool::shutdown]` — Idempotent: returns immediately if `stopped` is already `true`.

## Side Effects

- `[thread_pool.cpp:ThreadPool::ThreadPool]` — Spawns worker threads via `BS::thread_pool` and logs the active thread count via `Logger::info`.
- `[thread_pool.cpp:ThreadPool::shutdown]` — Sets `stopped = true`, transitions `g_game().setGameState(GAME_STATE_SHUTDOWN)`, destroys the underlying `BS::thread_pool` (`pool.reset()`, waiting for running tasks), and resets `SIGINT` and `SIGTERM` handlers to `SIG_DFL`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`

---

## Thread Pool Guide

The thread pool is a collection of threads that can be used to execute tasks.
The thread pool is created with a fixed number of threads. By default, the number of threads is the number of cpu cores.
The use can also specify the number of cores via `DEFAULT_NUMBER_OF_THREADS` environment variable.
The bigger value between the two is used.

Keep in mind that if the number of threads is too high, the performance will be degraded due to the context switching.

### Usage

The user can post tasks to the thread pool and the thread pool will execute them on one of its threads.

```cpp
#include "lib/thread/thread_pool.hpp"

int main() {
    ThreadPool &pool = inject<ThreadPool>(); // preferably uses constructor injection or setter injection.

    // Post a task to the thread pool
    pool.detach_task([]() {
        std::cout << "Hello from thread " << std::this_thread::get_id() << std::endl;
    });
}
```

### Parallelism
The load can be executed on any thread in the thread pool, meaning that they are trully asynchronous and parallel (if you have multiple cores).
This means that you should take care of the thread safety of your code, either with atomic variables or mutexes.

### Lifetime
We have a centralized thread pool via dependency injection. This means that the thread pool will be destroyed when the dependency injection container is destroyed.
This also mean that you cannot join threads, you need to rely on signals if you want to acknowledge that the a load executed.
