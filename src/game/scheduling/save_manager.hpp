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
	void scheduleAll();

	bool savePlayer(std::shared_ptr<Player> player, std::optional<Position> position = std::nullopt);
	void saveBotPosition(uint32_t guid, const Position& position);
	// Reuse unsaved bot state instead of loading older progression from the database.
	std::shared_ptr<Player> getPendingBotPlayer(uint32_t guid) const;
	std::shared_ptr<Player> getPendingBotPlayer(const std::string &name) const;
	void saveGuild(std::shared_ptr<Guild> guild);

private:
	struct BotSave {
		uint32_t guid = 0;
		std::shared_ptr<Player> player;
		Position position;
		std::shared_ptr<const PlayerSaveSnapshot> checkpoint;
	};
	struct SaveBatch {
		std::vector<std::pair<std::shared_future<bool>, std::string>> players;
		std::vector<std::shared_ptr<Guild>> guilds;
	};
	SaveBatch captureBatch(); // Dispatcher only; workers never inspect the engine.
	void saveBatch(SaveBatch batch);
	std::shared_future<bool> enqueueBot(BotSave save);
	void runBotSave(uint32_t guid);
	SerialSaveQueue<BotSave> botSaves_;
	// Bound DB connections and keep bot SQL from occupying the general worker pool.
	BS::thread_pool<BS::tp::none> botSavePool_ {4};
	void saveMap();
	void saveKV();

	void schedulePlayer(std::weak_ptr<Player> player);
	bool doSavePlayer(std::shared_ptr<Player> player, std::optional<Position> position = std::nullopt);

	phmap::parallel_flat_hash_map<uint32_t, std::chrono::steady_clock::time_point> m_playerMap;

	ThreadPool &threadPool;
	KVStore &kv;
	Logger &logger;
	Game &game;
};

constexpr auto g_saveManager = SaveManager::getInstance;
