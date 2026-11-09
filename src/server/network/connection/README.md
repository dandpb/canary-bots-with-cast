# Connection

## Overview
Manages asynchronous TCP client connections using ASIO (`asio::ip::tcp::socket` and `asio::high_resolution_timer`) and tracks active sessions via `ConnectionManager`. It handles socket lifecycle, proxy identification headers, packet framing, rate limiting, read/write timeouts, and dispatching incoming messages to the bound `Protocol` instance.

## Interface
- `ConnectionManager` (`[connection.hpp:ConnectionManager]`): Singleton manager (`getInstance()`, `createConnection()`, `releaseConnection()`, `closeAll()`) that creates, tracks, and closes active `Connection_ptr` instances in a thread-safe hash set (`[connection.hpp:ConnectionManager::connections]`).
- `Connection` (`[connection.hpp:Connection]`): Non-copyable shared-pointer-managed TCP session class exposing `accept(Protocol_ptr)`, `acceptInternal(bool)`, `resumeWork()`, `send(const OutputMessage_ptr &)`, `close(bool)`, and `getIP()`.
- Timeout constants: `CONNECTION_WRITE_TIMEOUT` (`[connection.hpp:CONNECTION_WRITE_TIMEOUT]`) and `CONNECTION_READ_TIMEOUT` (`[connection.hpp:CONNECTION_READ_TIMEOUT]`), both set to 30 seconds.

## Invariants
- `Connection` instances are non-copyable (`[connection.hpp:Connection]`) and managed via `std::enable_shared_from_this<Connection>` (`[connection.hpp:Connection]`).
- Thread-safe access to internal connection state, timers, and `messageQueue` is synchronized via `std::recursive_mutex connectionLock` (`[connection.hpp:Connection::connectionLock]`).
- Incoming packet payload sizes in `parseHeader` must be strictly greater than `0` and at most `INPUTMESSAGE_MAXSIZE`, otherwise the connection is force-closed (`[connection.cpp:Connection::parseHeader]`).
- Incoming packet rate is bounded by `MAX_PACKETS_PER_SECOND` from `g_configManager()`; exceeding this rate disconnects the client (`[connection.cpp:Connection::parseHeader]`).
- Once `connectionState` transitions to `CONNECTION_STATE_CLOSED`, subsequent `close()` and `send()` calls are no-ops (`[connection.cpp:Connection::close]`, `[connection.cpp:Connection::send]`).

## Side Effects
- Performs asynchronous network I/O (`asio::async_read`, `asio::async_write`, `asio::post`) and socket shutdown/close operations on `asio::ip::tcp::socket` (`[connection.cpp:Connection::acceptInternal]`, `[connection.cpp:Connection::internalSend]`, `[connection.cpp:Connection::closeSocket]`, `[connection.cpp:ConnectionManager::closeAll]`).
- Arms and cancels ASIO timers `readTimer` and `writeTimer`, force-closing timed-out connections via `Connection::handleTimeout` (`[connection.cpp:Connection::handleTimeout]`).
- Schedules protocol events (`sendLoginChallenge` and `release`) onto the global dispatcher `g_dispatcher()` (`[connection.cpp:Connection::accept]`, `[connection.cpp:Connection::close]`).
- Mutates the active connection registry in `ConnectionManager::connections` (`[connection.cpp:ConnectionManager::createConnection]`, `[connection.cpp:ConnectionManager::releaseConnection]`, `[connection.cpp:ConnectionManager::closeAll]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
