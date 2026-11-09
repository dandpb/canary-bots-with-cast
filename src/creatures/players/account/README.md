# Player Account Lock

## Overview
Provides a lightweight, process-local per-account concurrency guard (`AccountLocker` / `AccountLock`) used to serialize simultaneous login or account-mutation operations for the same `accountId` within the server process.

## Interface
- `AccountLocker` (`[account_lock.hpp:AccountLocker]`, `[account_lock.cpp:AccountLocker]`): Static lock manager providing `acquire(uint32_t accountId)` (`[account_lock.cpp:AccountLocker::acquire]`) and `isLocked(uint32_t accountId)` (`[account_lock.cpp:AccountLocker::isLocked]`).
- `AccountLock` (`[account_lock.hpp:AccountLock]`, `[account_lock.cpp:AccountLock]`): Move-only RAII token representing an active lock attempt for an `accountId`, exposing `acquired()`, `operator bool()`, and `id()` (`[account_lock.hpp:AccountLock::acquired]`).

## Invariants
- Only one `AccountLock` may hold `acquired_ == true` for a given `accountId` at any time; a concurrent `AccountLocker::acquire(accountId)` call while `accountId` is present in `activeAccountIds()` returns an `AccountLock` with `acquired() == false` (`[account_lock.cpp:AccountLocker::acquire]`).
- `AccountLock` is non-copyable (`[account_lock.hpp:AccountLock]`); moving an `AccountLock` transfers ownership and clears `acquired_` on the moved-from instance so only the final owner releases the lock upon destruction (`[account_lock.cpp:AccountLock::operator=]`, `[account_lock.cpp:AccountLock::~AccountLock]`).

## Side Effects
- Acquires a process-global `std::mutex` (`lockMutex()`) and mutates the static `phmap::flat_hash_set<uint32_t>` (`activeAccountIds()`) on lock acquisition and destruction (`[account_lock.cpp:AccountLocker::acquire]`, `[account_lock.cpp:AccountLocker::release]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
