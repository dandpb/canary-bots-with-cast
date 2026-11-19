/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#pragma once

#include "lib/thread/thread_pool.hpp"

#include <atomic>
#include <functional>
#include "game/scheduling/serial_save_queue.hpp"
#include "game/movement/position.hpp"

class KVStore;
class Logger;
class Game;
class Player;
class Guild;
struct PlayerSaveSnapshot;

class SaveManager {
public:
	explicit SaveManager(ThreadPool &threadPool, KVStore &kvStore, Logger &logger, Game &game);

	SaveManager(const SaveManager &) = delete;
	void operator=(const SaveManager &) = delete;

	static SaveManager &getInstance();

	void saveAll();
	void beginFinalSave();
	bool saveFinal(const std::function<bool()> &saveMotd);
	bool finalCommitUncertain() const { return finalCommitUncertain_.load(); }
	void scheduleAll();

	bool savePlayer(std::shared_ptr<Player> player, std::optional<Position> position = std::nullopt);
	void saveLogoutPlayer(const std::shared_ptr<Player> &player);
	bool hasPendingLogout(uint32_t guid) const;
	bool hasPendingLogout(const std::string &name) const;
	bool creditPendingLogout(uint32_t guid, uint64_t amount);
	void saveBotPosition(uint32_t guid, const Position& position);
	// Reuse unsaved bot state instead of loading older progression from the database.
	std::shared_ptr<Player> getPendingBotPlayer(uint32_t guid) const;
	std::shared_ptr<Player> getPendingBotPlayer(const std::string &name) const;
	bool saveGuild(std::shared_ptr<Guild> guild);

private:
	struct PlayerSave {
		uint32_t guid = 0;
		std::shared_ptr<Player> player;
		Position position;
		std::shared_ptr<const PlayerSaveSnapshot> checkpoint;
		std::string receipt;
		bool logout = false;
	};
	struct SaveBatch {
		std::vector<std::pair<std::shared_future<bool>, std::string>> players;
		std::vector<std::shared_ptr<Guild>> guilds;
		bool final = false;
	};
	SaveBatch captureBatch(); // Dispatcher only; workers never inspect the engine.
	bool saveBatch(SaveBatch batch);
	void captureCheckpoint(PlayerSave &save);
	std::shared_future<bool> enqueuePlayerSave(PlayerSave save);
	void runPlayerSave(uint32_t guid);
	SerialSaveQueue<PlayerSave> playerSaves_;
	// Bound DB connections and keep queued saves off the general worker pool.
	BS::thread_pool<BS::tp::none> playerSavePool_ {4};
	bool saveFinalStage(const std::string &stage, const std::function<bool()> &save);
	bool saveMap(bool final);
	bool saveKV(bool final);
	void observeFinalOutcome();
	std::atomic_bool finalSaving_ = false;
	std::atomic_bool finalCommitUncertain_ = false;
	std::string finalSaveToken_;
	std::unordered_map<uint32_t, PlayerSave> finalPlayers_;

	void schedulePlayer(std::weak_ptr<Player> player);
	bool doSavePlayer(std::shared_ptr<Player> player, std::optional<Position> position = std::nullopt);

	phmap::parallel_flat_hash_map<uint32_t, std::chrono::steady_clock::time_point> m_playerMap;

	ThreadPool &threadPool;
	KVStore &kv;
	Logger &logger;
	Game &game;
};

constexpr auto g_saveManager = SaveManager::getInstance;
