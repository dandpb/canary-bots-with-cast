# database

## Overview
Provides synchronous and asynchronous MySQL database connectivity, query execution, result set parsing, batched `INSERT`/upsert builders, RAII transaction management, schema version migrations, and a dedicated background worker thread/connection for bot-originated database tasks.

## Interface
- `Database` & `g_database` (`[database.hpp:Database]`, `[database.hpp:g_database]`): Core MySQL client wrapper supporting connection lifecycle (`[database.hpp:Database::connect]`), synchronous query execution (`[database.hpp:Database::executeQuery]`, `[database.hpp:Database::storeQuery]`, `[database.hpp:Database::retryQuery]`), SQL escaping (`[database.hpp:Database::escapeString]`, `[database.hpp:Database::escapeBlob]`), connection-free statement capture (`[database.hpp:Database::collectStatements]`, `[database.hpp:Database::isCapturingStatements]`), thread-local connection routing (`[database.hpp:Database::ScopedConnection]`), deadlock retry validation (`[database.hpp:Database::transactionContext]`, `[database.hpp:Database::canRetryDeadlock]`), and database backups (`[database.hpp:Database::createDatabaseBackup]`).
- `DBResult` & `DBResult_ptr` (`[database.hpp:DBResult]`, `[database.hpp:DBResult_ptr]`): Result set wrapper providing typed column extraction (`[database.hpp:DBResult::getNumber]`, `[database.hpp:DBResult::getString]`, `[database.hpp:DBResult::getStream]`, `[database.hpp:DBResult::getU8FromString]`, `[database.hpp:DBResult::getInt8FromString]`) and row iteration (`[database.hpp:DBResult::countResults]`, `[database.hpp:DBResult::hasNext]`, `[database.hpp:DBResult::next]`).
- `DBInsert` (`[database.hpp:DBInsert]`): Batched multi-row `INSERT` and `ON DUPLICATE KEY UPDATE` statement builder (`[database.hpp:DBInsert::addRow]`, `[database.hpp:DBInsert::upsert]`, `[database.hpp:DBInsert::execute]`).
- `DBTransaction` & `TransactionStates_t` (`[database.hpp:DBTransaction]`, `[database_definitions.hpp:TransactionStates_t]`): Scoped transaction helper executing callbacks within `BEGIN`/`COMMIT`/`ROLLBACK` blocks (`[database.hpp:DBTransaction::executeWithinTransaction]`).
- `DatabaseException` (`[database.hpp:DatabaseException]`): Exception type for database errors.
- `DbDispatcherStats` (`[database.hpp:DbDispatcherStats]`): Telemetry namespace tracking cumulative dispatcher-thread synchronous DB latency (`[database.hpp:DbDispatcherStats::addSyncDbUs]`, `[database.hpp:DbDispatcherStats::fetchResetSyncDbUs]`).
- `DatabaseManager` (`[databasemanager.hpp:DatabaseManager]`): Schema inspection, table optimization, and Lua migration runner (`[databasemanager.hpp:DatabaseManager::tableExists]`, `[databasemanager.hpp:DatabaseManager::isDatabaseSetup]`, `[databasemanager.hpp:DatabaseManager::getDatabaseVersion]`, `[databasemanager.hpp:DatabaseManager::optimizeTables]`, `[databasemanager.hpp:DatabaseManager::updateDatabase]`, `[databasemanager.hpp:DatabaseManager::getDatabaseConfig]`, `[databasemanager.hpp:DatabaseManager::registerDatabaseConfig]`).
- `DatabaseTasks` & `g_databaseTasks` (`[databasetasks.hpp:DatabaseTasks]`, `[databasetasks.hpp:g_databaseTasks]`): Thread-pool-backed asynchronous query executor (`[databasetasks.hpp:DatabaseTasks::execute]`, `[databasetasks.hpp:DatabaseTasks::store]`).
- `BotDatabaseTasks` & `g_botDatabaseTasks` (`[botdatabasetasks.hpp:BotDatabaseTasks]`, `[botdatabasetasks.hpp:g_botDatabaseTasks]`): Dedicated `std::jthread` and private `Database` connection for bot-originated async queries (`[botdatabasetasks.hpp:BotDatabaseTasks::execute]`, `[botdatabasetasks.hpp:BotDatabaseTasks::store]`).

## Invariants
- `Database::collectStatements` requires a fresh, unconnected `Database` instance (`handle == nullptr && statements_ == nullptr`) and throws `std::logic_error` otherwise; when capturing statements, `storeQuery` is forbidden and throws `std::logic_error` (`[database.hpp:Database::collectStatements]`, `[database.cpp:Database::storeQuery]`).
- `Database::beginTransaction` acquires `databaseLock` after executing `BEGIN`, and `commit`/`rollback` release `databaseLock` (`[database.cpp:Database::beginTransaction]`, `[database.cpp:Database::commit]`, `[database.cpp:Database::rollback]`).
- `Database::canRetryDeadlock` returns `true` only when the transaction occurred on the same `Database` instance, same MySQL thread ID, same `recoveryEpoch_`, and failed with MySQL deadlock error `1213` (`[database.cpp:Database::canRetryDeadlock]`).
- `DBInsert::execute` splits batched row values so each query never exceeds `Database::MAX_QUERY_SIZE` (8 MB) or `maxPacketSize` (`[database.hpp:Database::MAX_QUERY_SIZE]`, `[database.cpp:Database::addRow]`, `[database.cpp:DBInsert::execute]`).
- `BotDatabaseTasks` never touches the shared `Database` singleton or `ThreadPool`, isolating all bot async DB I/O onto its own `db_` connection and `worker_` thread (`[botdatabasetasks.hpp:BotDatabaseTasks]`, `[botdatabasetasks.cpp:BotDatabaseTasks::run]`).

## Side Effects
- Opens TCP/Unix socket connections to MySQL and executes SQL queries and transactions via `libmysqlclient` (`[database.cpp:Database::connect]`, `[database.cpp:Database::executeQuery]`, `[database.cpp:Database::storeQuery]`, `[database.cpp:Database::beginTransaction]`, `[database.cpp:Database::commit]`, `[database.cpp:Database::rollback]`).
- `Database::createDatabaseBackup` writes temporary credentials (`database_backup.cnf`), invokes `mysqldump` via `std::system`, compresses `.sql` dumps into `.sql.gz` under `database_backup/`, and deletes `.gz` backups older than 7 days (`[database.cpp:Database::createDatabaseBackup]`).
- `DatabaseManager::updateDatabase` creates a Lua state, scans and executes migration scripts in `<DATA_DIRECTORY>/migrations/`, and updates `server_config` (`[databasemanager.cpp:DatabaseManager::updateDatabase]`).
- `DatabaseTasks` and `BotDatabaseTasks` dispatch completion callbacks onto `g_dispatcher()` (`[databasetasks.cpp:DatabaseTasks::execute]`, `[databasetasks.cpp:DatabaseTasks::store]`, `[botdatabasetasks.cpp:BotDatabaseTasks::run]`).
- Records lock and query latency metrics (`metrics::lock_latency`, `metrics::query_latency`) and dispatcher sync DB telemetry gated by `BOT_PERF_TELEMETRY=1` (`[database.cpp:SyncDbTimer]`, `[database.cpp:Database::executeQuery]`, `[database.cpp:Database::storeQuery]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
