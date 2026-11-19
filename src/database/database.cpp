/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "database/database.hpp"

#include "config/configmanager.hpp"
#include "game/scheduling/dispatcher.hpp"
#include "lib/di/container.hpp"
#include "lib/metrics/metrics.hpp"
#include "utils/tools.hpp"

#include <atomic>
#include <cstdlib>

#ifndef _WIN32
	#include <poll.h>
#endif
#include <chrono> // dbMonoMs (JITTER FIX 2026-06-10) — explicit, don't rely on PCH

thread_local std::pair<const Database*, unsigned int> Database::lastExecuteError_ {nullptr, 0};
thread_local uint64_t Database::recoveryEpoch_ = 0;

// PERF_INVESTIGATION_2026-05-24 pre-flight telemetry — log the first N sync
// DB queries that fire on the dispatcher thread. Goal: identify which Lua /
// C++ callsite is producing the hash_sparse 58.83% / pvio_socket_wait_io
// 8.06% post-stall samples. Gated by BOT_PERF_TELEMETRY=1.
namespace {
bool dbPerfTelemetryEnabled() {
	static const bool enabled = []() {
		const char* v = std::getenv("BOT_PERF_TELEMETRY");
		return v != nullptr && v[0] == '1';
	}();
	return enabled;
}

int64_t dbMonoUs() {
	return std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
}

std::atomic<int64_t> s_dispatcherSyncDbUs { 0 };

// JITTER FIX 2026-06-10: uncapped, duration-thresholded sync-query telemetry.
// The first-300 capture above goes silent ~2h into uptime (cap exhausted by the
// 10s bot_commands poll), leaving afternoon stall windows blind. This timer fires
// for the whole process lifetime whenever a sync query issued FROM THE DISPATCHER
// THREAD takes >10ms — measured across databaseLock acquisition + the query, so
// head-of-line blocking behind a worker-thread transaction shows up here too.
using SqlClock = std::chrono::steady_clock;
constexpr auto DispatcherSqlBudget = std::chrono::milliseconds(1500);

template <typename Continue>
bool awaitSql(MYSQL *connection, int waiting, SqlClock::time_point deadline, Continue resume) {
	while (waiting) {
		auto remaining = std::chrono::ceil<std::chrono::milliseconds>(deadline - SqlClock::now()).count();
		if (remaining <= 0) return false;
		if (waiting & MYSQL_WAIT_TIMEOUT) {
			remaining = std::min(remaining, static_cast<decltype(remaining)>(mysql_get_timeout_value_ms(connection)));
		}
		short events = 0;
		if (waiting & MYSQL_WAIT_READ) events |= POLLIN;
		if (waiting & MYSQL_WAIT_WRITE) events |= POLLOUT;
		if (waiting & MYSQL_WAIT_EXCEPT) events |= POLLPRI;
#ifdef _WIN32
		WSAPOLLFD descriptor { mysql_get_socket(connection), events, 0 };
		const int ready = WSAPoll(&descriptor, 1, static_cast<int>(remaining));
#else
		pollfd descriptor { mysql_get_socket(connection), events, 0 };
		const int ready = poll(&descriptor, 1, static_cast<int>(remaining));
#endif
		if (ready < 0 || SqlClock::now() >= deadline) return false;
		int activity = 0;
		if (ready == 0) {
			if (!(waiting & MYSQL_WAIT_TIMEOUT)) return false;
			activity = MYSQL_WAIT_TIMEOUT;
		} else {
			if (descriptor.revents & (POLLERR | POLLHUP | POLLNVAL)) return false;
			if (descriptor.revents & POLLIN) activity |= MYSQL_WAIT_READ;
			if (descriptor.revents & POLLOUT) activity |= MYSQL_WAIT_WRITE;
			if (descriptor.revents & POLLPRI) activity |= MYSQL_WAIT_EXCEPT;
		}
		waiting = resume(activity);
	}
	return true;
}

struct SyncDbTimer {
	const char* kind;
	std::string_view query;
	int64_t start = 0;
	bool active = false;
	SyncDbTimer(const char* k, std::string_view q) :
		kind(k), query(q) {
		if (dbPerfTelemetryEnabled() && Dispatcher::isOnDispatcherThread()) {
			active = true;
			start = dbMonoUs();
		}
	}
	~SyncDbTimer() {
		if (!active) {
			return;
		}
		int64_t dt_us = dbMonoUs() - start;
		// Bundle 4: ALWAYS accumulate into the per-cycle dispatcher counter (drained
		// by the dispatcher loop into CYCLE_SLOW dbsync=) — many sub-10ms queries
		// convoying behind worker traffic are invisible to the threshold log below.
		s_dispatcherSyncDbUs.fetch_add(dt_us, std::memory_order_relaxed);
		if (dt_us > 10000) {
			g_logger().warn("[DB_SYNC_SLOW] kind={} duration={}ms (incl. lock wait) query=\"{}\"",
				kind, dt_us / 1000, query.substr(0, 160));
		}
	}
};
}

void DbDispatcherStats::addSyncDbUs(int64_t us) {
	s_dispatcherSyncDbUs.fetch_add(us, std::memory_order_relaxed);
}

int64_t DbDispatcherStats::fetchResetSyncDbUs() {
	return s_dispatcherSyncDbUs.exchange(0, std::memory_order_relaxed);
}

namespace { thread_local Database* scopedConnection_ = nullptr; }

Database::ScopedConnection::ScopedConnection(Database& connection) : previous_(scopedConnection_) {
	scopedConnection_ = &connection;
}

Database::ScopedConnection::~ScopedConnection() { scopedConnection_ = previous_; }

Database::~Database() {
	if (handle != nullptr) {
		mysql_close(handle);
	}
}

Database &Database::getInstance() {
	if (scopedConnection_) return *scopedConnection_;
	return inject<Database>();
}

bool Database::connect() {
	return connect(&g_configManager().getString(MYSQL_HOST), &g_configManager().getString(MYSQL_USER), &g_configManager().getString(MYSQL_PASS), &g_configManager().getString(MYSQL_DB), g_configManager().getNumber(SQL_PORT), &g_configManager().getString(MYSQL_SOCK));
}

bool Database::connect(const std::string* host, const std::string* user, const std::string* password, const std::string* database, uint32_t port, const std::string* sock) {
	std::unique_lock lock(databaseLock, std::defer_lock);
	if (!lockForOperation(lock) || transactionActive) {
		return false;
	}
	discardConnection();
	connectionOptions = ConnectionOptions { *host, *user, *password, *database, *sock, port };
	if (!openConnection()) {
		return false;
	}
	if (const auto result = storeQuery("SHOW VARIABLES LIKE 'max_allowed_packet'")) {
		maxPacketSize = result->getNumber<uint64_t>("Value");
	}
	return handle != nullptr;
}

bool Database::openConnection() {
	if (!connectionOptions || transactionActive) {
		return false;
	}
	const auto &options = *connectionOptions;
	handle = mysql_init(nullptr);
	if (!handle) {
		g_logger().error("Failed to initialize MySQL connection handle");
		return false;
	}

	// Replacing the transport must be explicit. Implicit reconnect can execute
	// a later statement in autocommit after the server has rolled back the transaction.
	bool disabled = false;
	unsigned int timeoutSeconds = 1;
	mysql_options(handle, MYSQL_OPT_RECONNECT, &disabled);
	mysql_options(handle, MYSQL_OPT_NONBLOCK, nullptr);
	mysql_options(handle, MYSQL_OPT_CONNECT_TIMEOUT, &timeoutSeconds);
	mysql_options(handle, MYSQL_OPT_READ_TIMEOUT, &timeoutSeconds);
	mysql_options(handle, MYSQL_OPT_WRITE_TIMEOUT, &timeoutSeconds);
	mysql_options(handle, MYSQL_OPT_SSL_VERIFY_SERVER_CERT, &disabled);
	if (!mysql_real_connect(handle, options.host.c_str(), options.user.c_str(), options.password.c_str(),
		options.database.c_str(), options.port, options.socket.c_str(), 0)) {
		g_logger().error("MySQL connection failed [{}]", mysql_errno(handle));
		discardConnection();
		return false;
	}
	return true;
}

void Database::discardConnection() {
	if (handle) {
		mysql_close(std::exchange(handle, nullptr));
		++recoveryEpoch_;
	}
}

bool Database::lockForOperation(std::unique_lock<std::recursive_mutex> &lock) const {
	if (Dispatcher::isOnDispatcherThread()) {
		return lock.try_lock();
	}
	lock.lock();
	return true;
}

bool Database::isConnected() const {
	std::unique_lock lock(databaseLock, std::defer_lock);
	return lockForOperation(lock) && handle;
}

bool Database::readyForQuery() {
	if (transactionActive) {
		return handle && !transactionFailed;
	}
	if (handle) {
		return true;
	}
	// Reserve the dispatcher's current operation for recovery. A subsequent
	// invocation can use the new connection without spending two I/O budgets.
	return openConnection() && !Dispatcher::isOnDispatcherThread();
}

void Database::createDatabaseBackup(bool compress) const {
	if (!g_configManager().getBoolean(MYSQL_DB_BACKUP)) {
		return;
	}

	// Get current time for formatting
	auto now = std::chrono::system_clock::now();
	std::string formattedDate = fmt::format("{:%Y-%m-%d}", now);
	std::string formattedTime = fmt::format("{:%H-%M-%S}", now);

	// Create a backup directory based on the current date
	std::string backupDir = fmt::format("database_backup/{}/", formattedDate);
	std::filesystem::create_directories(backupDir);
	std::string backupFileName = fmt::format("{}backup_{}.sql", backupDir, formattedTime);

	// Create a temporary configuration file for MySQL credentials
	std::string tempConfigFile = "database_backup.cnf";
	std::ofstream configFile(tempConfigFile);
	if (configFile.is_open()) {
		configFile << "[client]\n";
		configFile << "user=\"" << g_configManager().getString(MYSQL_USER) << "\"\n";
		configFile << "password=\"" << g_configManager().getString(MYSQL_PASS) << "\"\n";
		configFile << "host=" << g_configManager().getString(MYSQL_HOST) << "\n";
		configFile << "port=" << g_configManager().getNumber(SQL_PORT) << "\n";
		configFile.close();
	} else {
		g_logger().error("Failed to create temporary MySQL configuration file.");
		return;
	}

	// Execute mysqldump command to create backup file
	std::string command = fmt::format(
		"mysqldump --defaults-extra-file={} {} > {}",
		tempConfigFile, g_configManager().getString(MYSQL_DB), backupFileName
	);

	int result = std::system(command.c_str());
	std::filesystem::remove(tempConfigFile);

	if (result != 0) {
		g_logger().error("Failed to create database backup using mysqldump.");
		return;
	}

	// Compress the backup file if requested
	std::string compressedFileName;
	compressedFileName = backupFileName + ".gz";
	gzFile gzFile = gzopen(compressedFileName.c_str(), "wb9");
	if (!gzFile) {
		g_logger().error("Failed to open gzip file for compression.");
		return;
	}

	std::ifstream backupFile(backupFileName, std::ios::binary);
	if (!backupFile.is_open()) {
		g_logger().error("Failed to open backup file for compression: {}", backupFileName);
		gzclose(gzFile);
		return;
	}

	std::string buffer(8192, '\0');
	while (backupFile.read(&buffer[0], buffer.size()) || backupFile.gcount() > 0) {
		gzwrite(gzFile, buffer.data(), backupFile.gcount());
	}

	backupFile.close();
	gzclose(gzFile);
	std::filesystem::remove(backupFileName);

	g_logger().info("Database backup successfully compressed to: {}", compressedFileName);

	// Delete backups older than 7 days
	auto nowTime = std::chrono::system_clock::now();
	auto sevenDaysAgo = nowTime - std::chrono::hours(7 * 24); // 7 days in hours
	for (const auto &entry : std::filesystem::directory_iterator("database_backup")) {
		if (entry.is_directory()) {
			try {
				for (const auto &file : std::filesystem::directory_iterator(entry)) {
					if (file.path().extension() == ".gz") {
						auto fileTime = std::filesystem::last_write_time(file);
						auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(fileTime - std::filesystem::file_time_type::clock::now() + std::chrono::system_clock::now());
						auto fileTimeSystemClock = std::chrono::system_clock::time_point { sctp.time_since_epoch() };

						if (fileTimeSystemClock < sevenDaysAgo) {
							std::filesystem::remove(file);
							g_logger().info("Deleted old backup file: {}", file.path().string());
						}
					}
				}
			} catch (const std::filesystem::filesystem_error &e) {
				g_logger().error("Failed to check or delete files in backup directory: {}. Error: {}", entry.path().string(), e.what());
			}
		}
	}
}

bool Database::beginTransaction() {
	if (transactionActive || !readyForQuery() || !sendQuery("BEGIN")) {
		return false;
	}
	transactionActive = true;
	transactionFailed = false;
	return true;
}

Database::TransactionOutcome Database::finishTransaction(bool commit) {
	transactionActive = false;
	if (!handle) {
		// The body lost its connection before we sent COMMIT.
		return TransactionOutcome::Failed;
	}
	if (!commit || transactionFailed) {
		if (mysql_rollback(handle) != 0) {
			discardConnection();
		}
		return TransactionOutcome::Failed;
	}
	if (mysql_commit(handle) == 0) {
		return TransactionOutcome::Committed;
	}
	const auto error = mysql_errno(handle);
	const bool uncertain = isRecoverableError(error);
	g_logger().error("MySQL commit failed [{}], outcome {}", error, uncertain ? "uncertain" : "failed");
	if (uncertain || mysql_rollback(handle) != 0) {
		discardConnection();
	}
	return uncertain ? TransactionOutcome::Uncertain : TransactionOutcome::Failed;
}

bool DBTransaction::prepareReceipt(Database &database, bool &alreadyCommitted) {
	const auto key = database.escapeString(receipt_->key);
	// Lock the same row as the previous attempt before deciding whether it committed.
	if (!database.executeQuery(fmt::format(
			"INSERT INTO `server_config` (`config`, `value`) VALUES ({}, '') "
			"ON DUPLICATE KEY UPDATE `config` = `config`", key))) {
		return false;
	}
	const auto row = database.storeQuery(fmt::format(
		"SELECT `value` FROM `server_config` WHERE `config` = {} FOR UPDATE", key));
	if (!row) return false;
	alreadyCommitted = row->getString("value") == receipt_->token;
	return alreadyCommitted || database.executeQuery(fmt::format(
		"UPDATE `server_config` SET `value` = {} WHERE `config` = {}", database.escapeString(receipt_->token), key));
}

bool Database::isRecoverableError(unsigned int error) {
	return error == CR_SERVER_LOST || error == CR_SERVER_GONE_ERROR || error == CR_CONN_HOST_ERROR || error == 1053 /*ER_SERVER_SHUTDOWN*/ || error == CR_CONNECTION_ERROR;
}

unsigned int Database::getLastExecuteError() const {
	return lastExecuteError_.first == this ? lastExecuteError_.second : 0;
}

Database::TransactionContext Database::transactionContext() const {
	std::unique_lock lock(databaseLock, std::defer_lock);
	if (!lockForOperation(lock)) {
		return {this, 0, recoveryEpoch_};
	}
	return {this, handle ? static_cast<uint64_t>(mysql_thread_id(handle)) : 0, recoveryEpoch_};
}

bool Database::canRetryDeadlock(const TransactionContext& context) const {
	std::unique_lock lock(databaseLock, std::defer_lock);
	return lockForOperation(lock) && context.owner == this && context.connectionId != 0 && handle
		&& context.connectionId == static_cast<uint64_t>(mysql_thread_id(handle))
		&& context.recoveryEpoch == recoveryEpoch_ && getLastExecuteError() == 1213;
}

void Database::recordQueryFailure(unsigned int error) {
	lastExecuteError_ = {this, error};
	transactionFailed = transactionActive;
	g_logger().error("MySQL statement failed [{}]", error);
	if (isRecoverableError(error)) {
		discardConnection();
	}
}

bool Database::sendQuery(std::string_view query) {
	lastExecuteError_ = {this, 0};
	if (mysql_real_query(handle, query.data(), query.size()) == 0) {
		return true;
	}
	recordQueryFailure(mysql_errno(handle));
	return false;
}

bool Database::executeQuery(std::string_view query) {
	if (statements_) {
		statements_->emplace_back(query);
		return true;
	}

	SyncDbTimer syncTimer("execute", query);
	metrics::lock_latency measureLock("database");
	std::unique_lock lock(databaseLock, std::defer_lock);
	if (!lockForOperation(lock)) {
		return false;
	}
	measureLock.stop();

	metrics::query_latency measure(query.substr(0, 50));
	if (!readyForQuery() || !sendQuery(query)) {
		return false;
	}
	if (auto *result = mysql_store_result(handle)) {
		mysql_free_result(result);
	} else if (mysql_field_count(handle) != 0) {
		recordQueryFailure(mysql_errno(handle));
		return false;
	}
	return true;
}

DBResult_ptr Database::storeQuery(std::string_view query) {
	bool success;
	return storeQuery(query, success);
}

DBResult_ptr Database::storeQuery(std::string_view query, bool &success) {
	const auto deadline = SqlClock::now() + DispatcherSqlBudget;
	success = false;
	if (statements_) {
		throw std::logic_error("A player checkpoint cannot perform database reads");
	}
	SyncDbTimer syncTimer("store", query);
	metrics::lock_latency measureLock("database");
	std::unique_lock lock(databaseLock, std::defer_lock);
	if (!lockForOperation(lock)) {
		return nullptr;
	}
	measureLock.stop();

	metrics::query_latency measure(query.substr(0, 50));
	if (!readyForQuery()) return nullptr;
	MYSQL_RES *result = nullptr;
	if (Dispatcher::isOnDispatcherThread()) {
		int status = 0;
		lastExecuteError_ = {this, 0};
		int waiting = mysql_real_query_start(&status, handle, query.data(), query.size());
		if (!awaitSql(handle, waiting, deadline, [&](int activity) {
			return mysql_real_query_cont(&status, handle, activity);
		})) {
			recordQueryFailure(CR_SERVER_LOST);
			return nullptr;
		}
		if (status != 0) {
			recordQueryFailure(mysql_errno(handle));
			return nullptr;
		}
		waiting = mysql_store_result_start(&result, handle);
		if (!awaitSql(handle, waiting, deadline, [&](int activity) {
			return mysql_store_result_cont(&result, handle, activity);
		})) {
			recordQueryFailure(CR_SERVER_LOST);
			return nullptr;
		}
	} else {
		if (!sendQuery(query)) return nullptr;
		result = mysql_store_result(handle);
	}
	if (result) {
		auto rows = std::make_shared<DBResult>(result);
		success = true;
		return rows->hasNext() ? rows : nullptr;
	}
	if (mysql_field_count(handle) != 0) {
		recordQueryFailure(mysql_errno(handle));
		return nullptr;
	}
	success = true;
	return nullptr;
}

std::string Database::escapeString(const std::string &s) const {
	std::string::size_type len = s.length();
	auto length = static_cast<uint32_t>(len);
	std::string escaped = escapeBlob(s.c_str(), length);
	if (escaped.empty()) {
		g_logger().warn("Error escaping string");
	}
	return escaped;
}

std::string Database::escapeBlob(const char* s, uint32_t length) const {
	std::unique_lock lock(databaseLock, std::defer_lock);
	if (statements_ || !lockForOperation(lock) || !handle) {
		// Hex literals preserve arbitrary bytes without a connection, charset state,
		// SQL-mode-dependent escaping, or a lock on the dispatcher's live connection.
		constexpr char hex[] = "0123456789ABCDEF";
		std::string literal = "X'";
		literal.reserve(2 * static_cast<size_t>(length) + 3);
		for (uint32_t i = 0; i < length; ++i) {
			const auto byte = static_cast<unsigned char>(s[i]);
			literal += hex[byte >> 4];
			literal += hex[byte & 15];
		}
		return literal + "'";
	}
	size_t maxLength = (length * 2) + 1;

	std::string escaped;
	escaped.reserve(maxLength + 2);
	escaped.push_back('\'');

	if (length != 0) {
		std::string output(maxLength, '\0');
		size_t escapedLength = mysql_real_escape_string(handle, &output[0], s, length);
		output.resize(escapedLength);
		escaped.append(output);
	}

	escaped.push_back('\'');
	return escaped;
}

DBResult::DBResult(MYSQL_RES* res) {
	handle = res;

	int num_fields = mysql_num_fields(handle);

	const MYSQL_FIELD* fields = mysql_fetch_fields(handle);
	for (size_t i = 0; i < num_fields; i++) {
		listNames[fields[i].name] = i;
	}
	row = mysql_fetch_row(handle);
}

DBResult::~DBResult() {
	mysql_free_result(handle);
}

std::string DBResult::getString(const std::string &s) const {
	auto it = listNames.find(s);
	if (it == listNames.end()) {
		g_logger().error("Column '{}' does not exist in result set", s);
		return {};
	}
	if (row[it->second] == nullptr) {
		return {};
	}
	return std::string(row[it->second]);
}

const char* DBResult::getStream(const std::string &s, unsigned long &size) const {
	auto it = listNames.find(s);
	if (it == listNames.end()) {
		g_logger().error("Column '{}' doesn't exist in the result set", s);
		size = 0;
		return nullptr;
	}

	if (row[it->second] == nullptr) {
		size = 0;
		return nullptr;
	}

	size = mysql_fetch_lengths(handle)[it->second];
	return row[it->second];
}

uint8_t DBResult::getU8FromString(const std::string &string, const std::string &function) {
	auto result = static_cast<uint8_t>(std::atoi(string.c_str()));
	if (result > std::numeric_limits<uint8_t>::max()) {
		g_logger().error("[{}] Failed to get number value {} for tier table result, on function call: {}", __FUNCTION__, result, function);
		return 0;
	}

	return result;
}

int8_t DBResult::getInt8FromString(const std::string &string, const std::string &function) {
	auto result = static_cast<int8_t>(std::atoi(string.c_str()));
	if (result > std::numeric_limits<int8_t>::max()) {
		g_logger().error("[{}] Failed to get number value {} for tier table result, on function call: {}", __FUNCTION__, result, function);
		return 0;
	}

	return result;
}

size_t DBResult::countResults() const {
	return static_cast<size_t>(mysql_num_rows(handle));
}

bool DBResult::hasNext() const {
	return row != nullptr;
}

bool DBResult::next() {
	if (!handle) {
		g_logger().error("Database not initialized!");
		return false;
	}
	row = mysql_fetch_row(handle);
	return row != nullptr;
}

DBInsert::DBInsert(std::string insertQuery) :
	query(std::move(insertQuery)) {
	this->length = this->query.length();
}

bool DBInsert::addRow(std::string_view row) {
	const size_t rowLength = row.length();
	length += rowLength;
	auto max_packet_size = Database::getInstance().getMaxPacketSize();

	if (length > max_packet_size && !execute()) {
		return false;
	}

	if (values.empty()) {
		values.reserve(rowLength + 2);
		values.push_back('(');
		values.append(row);
		values.push_back(')');
	} else {
		values.reserve(values.length() + rowLength + 3);
		values.push_back(',');
		values.push_back('(');
		values.append(row);
		values.push_back(')');
	}
	return true;
}

bool DBInsert::addRow(std::ostringstream &row) {
	bool ret = addRow(row.str());
	row.str(std::string());
	return ret;
}

void DBInsert::upsert(const std::vector<std::string> &columns) {
	upsertColumns = columns;
}

bool DBInsert::execute() {
	if (values.empty()) {
		return true;
	}

	std::string baseQuery = this->query;
	std::string upsertQuery;

	if (!upsertColumns.empty()) {
		std::ostringstream upsertStream;
		upsertStream << " ON DUPLICATE KEY UPDATE ";
		for (size_t i = 0; i < upsertColumns.size(); ++i) {
			upsertStream << "`" << upsertColumns[i] << "` = VALUES(`" << upsertColumns[i] << "`)";
			if (i < upsertColumns.size() - 1) {
				upsertStream << ", ";
			}
		}
		upsertQuery = upsertStream.str();
	}

	std::string currentBatch = values;
	while (!currentBatch.empty()) {
		size_t cutPos = Database::MAX_QUERY_SIZE - baseQuery.size() - upsertQuery.size();
		if (cutPos < currentBatch.size()) {
			cutPos = currentBatch.rfind("),(", cutPos);
			if (cutPos == std::string::npos) {
				return false;
			}
			cutPos += 2;
		} else {
			cutPos = currentBatch.size();
		}

		std::string batchValues = currentBatch.substr(0, cutPos);
		if (batchValues.back() == ',') {
			batchValues.pop_back();
		}
		currentBatch = currentBatch.substr(cutPos);

		std::ostringstream query;
		query << baseQuery << " " << batchValues << upsertQuery;
		if (!Database::getInstance().executeQuery(query.str())) {
			return false;
		}
	}

	return true;
}
