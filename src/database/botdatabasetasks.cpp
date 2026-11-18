/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "database/botdatabasetasks.hpp"

#include "game/scheduling/dispatcher.hpp"

#include <chrono>

BotDatabaseTasks &g_botDatabaseTasks() {
	static BotDatabaseTasks instance;
	return instance;
}

BotDatabaseTasks::~BotDatabaseTasks() {
	if (worker_.joinable()) {
		worker_.request_stop();
		cv_.notify_all();
	}
	// std::jthread joins in its destructor.
}

void BotDatabaseTasks::ensureStartedLocked() {
	if (started_) {
		return;
	}
	started_ = true;
	worker_ = std::jthread([this](const std::stop_token &token) { run(token); });
}

void BotDatabaseTasks::execute(const std::string &query, const std::function<void(DBResult_ptr, bool)> &callback /* nullptr */) {
	{
		std::scoped_lock lock(mutex_);
		ensureStartedLocked();
		queue_.push_back(Job { query, callback, false });
	}
	cv_.notify_one();
}

void BotDatabaseTasks::store(const std::string &query, const std::function<void(DBResult_ptr, bool)> &callback /* nullptr */) {
	{
		std::scoped_lock lock(mutex_);
		ensureStartedLocked();
		queue_.push_back(Job { query, callback, true });
	}
	cv_.notify_one();
}

void BotDatabaseTasks::run(const std::stop_token &token) {
	using Clock = std::chrono::steady_clock;
	constexpr auto reconnectInterval = std::chrono::seconds(2);
	auto nextConnect = Clock::now();
	bool connected = false;
	while (true) {
		Job job;
		{
			std::unique_lock lock(mutex_);
			cv_.wait(lock, [&] { return token.stop_requested() || !queue_.empty(); });
			if (token.stop_requested()) {
				return; // process teardown — drop any remainder, mirrors DatabaseTasks pool teardown
			}
			if (!connected && Clock::now() < nextConnect) {
				cv_.wait_until(lock, nextConnect, [&] { return token.stop_requested(); });
				if (token.stop_requested()) return;
			}
			job = std::move(queue_.front());
			queue_.pop_front();
		}

		if (!connected && Clock::now() >= nextConnect) {
			connected = db_.connect();
			nextConnect = Clock::now() + reconnectInterval;
			if (connected) {
				g_logger().info("[BotDatabaseTasks] dedicated database connection ready");
			}
		}

		DBResult_ptr result;
		bool success = false;
		if (connected) {
			if (job.isStore) {
				result = db_.storeQuery(job.query, success);
			} else {
				success = db_.executeQuery(job.query);
			}
			connected = db_.isConnected();
		}
		if (job.callback) {
			g_dispatcher().addEvent([callback = std::move(job.callback), result = std::move(result), success]() {
				callback(result, success);
			}, "BotDatabaseTasks::complete");
		}
	}
}
