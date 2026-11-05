/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "game/scheduling/save_manager.hpp"

#include "config/configmanager.hpp"
#include "creatures/players/grouping/guild.hpp"
#include "game/game.hpp"
#include "creatures/players/bot/bot_engine.hpp"
#include "io/ioguild.hpp"
#include "io/iologindata.hpp"
#include "kv/kv.hpp"
#include "lib/di/container.hpp"
#include "creatures/players/player.hpp"
#include "utils/tools.hpp"

void checkpointBotReloadPlayers(const BotReloadSnapshot& snapshot) {
	for (const auto& entry : snapshot.entries) {
		if (entry.player) g_saveManager().savePlayer(entry.player, entry.position);
	}
}

std::shared_ptr<Player> SaveManager::getPendingBotPlayer(uint32_t guid) const {
	auto pending = botSaves_.find(guid);
	return pending ? pending->player : nullptr;
}

std::shared_ptr<Player> SaveManager::getPendingBotPlayer(const std::string &name) const {
	const auto normalized = asLowerCaseString(name);
	for (const auto& pending : botSaves_.snapshot()) {
		if (pending.player && asLowerCaseString(pending.player->getName()) == normalized) return pending.player;
	}
	return nullptr;
}

SaveManager::SaveManager(ThreadPool &threadPool, KVStore &kvStore, Logger &logger, Game &game) :
	threadPool(threadPool), kv(kvStore), logger(logger), game(game) { }

SaveManager &SaveManager::getInstance() {
	return inject<SaveManager>();
}

SaveManager::SaveBatch SaveManager::captureBatch() {
	Benchmark captureTimer;
	// Capture strong references and position policy on the dispatcher, before any SQL.
	std::unordered_map<uint32_t, BotSave> captured;
	for (const auto& [_, player] : game.getPlayers()) {
		captured[player->getGUID()] = {player->getGUID(), player, player->getPosition()};
	}
	if (auto* engine = getBotEngineIfLoaded()) {
		for (const auto& snapshot : engine->capturePersistentPlayers()) {
			const auto guid = snapshot.player->getGUID();
			captured[guid] = {guid, snapshot.player, snapshot.loginPosition};
		}
	}
	for (const auto& pending : botSaves_.snapshot()) captured.try_emplace(pending.guid, pending);
	SaveBatch batch;
	for (const auto& [guid, save] : captured) {
		if (!save.player || save.player->isBotPlayer()) {
			batch.players.emplace_back(enqueueBot(save), save.player ? save.player->getName() : std::to_string(guid));
		} else {
			save.player->loginPosition = save.position;
			batch.players.emplace_back(threadPool.submit_task([this, player = save.player] {
				return doSavePlayer(player);
			}).share(), save.player->getName());
		}
	}
	for (const auto& [_, guild] : game.getGuilds()) batch.guilds.push_back(guild);
	logger.info("Captured {} players for server save in {} milliseconds", captured.size(), captureTimer.duration());
	return batch;
}

void SaveManager::saveBatch(SaveBatch batch) {
	Benchmark timer;
	size_t failures = 0;
	for (auto& [future, name] : batch.players) {
		try {
			if (!future.get()) { ++failures; logger.error("Failed to durably save player {}", name); }
		} catch (const std::exception& error) {
			++failures;
			logger.error("Failed to durably save player {}: {}", name, error.what());
		}
	}
	for (const auto& guild : batch.guilds) saveGuild(guild);
	saveMap();
	saveKV();
	if (failures) logger.error("Server save completed with {} player failures; bot state remains pending", failures);
	else logger.info("Server saved {} players in {} milliseconds", batch.players.size(), timer.duration());
}

void SaveManager::saveAll() { saveBatch(captureBatch()); }

void SaveManager::scheduleAll() {
	// Dependencies are queued before the batch waiter on the FIFO worker pool.
	// Neither the waiter nor a save worker consults the unloadable bot engine.
	auto batch = captureBatch();
	if (!g_configManager().getBoolean(TOGGLE_SAVE_ASYNC)) { saveBatch(std::move(batch)); return; }
	threadPool.detach_task([this, batch = std::move(batch)]() mutable { saveBatch(std::move(batch)); });
}

std::shared_future<bool> SaveManager::enqueueBot(BotSave save) {
	const auto guid = save.guid;
	auto requested = botSaves_.request(guid, std::move(save));
	if (requested.start) botSavePool_.detach_task([this, guid] { runBotSave(guid); });
	return requested.completed;
}

void SaveManager::runBotSave(uint32_t guid) {
	// Keep a transaction off the dispatcher's main DB connection. TLS belongs
	// to the executable and cannot retain an unloaded engine's code.
	thread_local std::unique_ptr<Database> connection;
	while (auto work = botSaves_.take(guid)) {
		bool success = false;
		try {
			if (!connection) {
				auto candidate = std::make_unique<Database>();
				if (!candidate->connect()) throw std::runtime_error("bot save DB connection unavailable");
				connection = std::move(candidate);
			}
			Database::ScopedConnection route(*connection);
			if (work->value.player) success = doSavePlayer(work->value.player, work->value.position);
			else {
				const auto& pos = work->value.position;
				success = Database::getInstance().executeQuery(fmt::format(
					"UPDATE `players` SET `posx`={}, `posy`={}, `posz`={} WHERE `id`={}", pos.x, pos.y, pos.z, guid));
			}
		} catch (const std::exception& error) {
			logger.error("Bot save failed for {}: {}", guid, error.what());
		} catch (...) { logger.error("Bot save failed for {} with an unknown exception", guid); }
		if (!botSaves_.finish(guid, work->generation, success)) break;
	}
}

void SaveManager::saveBotPosition(uint32_t guid, const Position& position) {
	// Dispatcher only. Preserve a pending full character save when updating position.
	enqueueBot({guid, getPendingBotPlayer(guid), position});
}

void SaveManager::schedulePlayer(std::weak_ptr<Player> playerPtr) {
	auto playerToSave = playerPtr.lock();
	if (!playerToSave) {
		logger.debug("Skipping save for player because player is no longer online.");
		return;
	}

	if (playerToSave->isBotPlayer()) {
		enqueueBot({playerToSave->getGUID(), playerToSave, playerToSave->getLoginPosition()});
		return;
	}

	// Disable save async if the config is set to false
	if (!g_configManager().getBoolean(TOGGLE_SAVE_ASYNC)) {
		if (g_game().getGameState() == GAME_STATE_NORMAL) {
			logger.debug("Saving player {}.", playerToSave->getName());
		}
		doSavePlayer(playerToSave);
		return;
	}

	logger.debug("Scheduling player {} for saving.", playerToSave->getName());
	auto scheduledAt = std::chrono::steady_clock::now();
	m_playerMap[playerToSave->getGUID()] = scheduledAt;
	threadPool.detach_task([this, playerPtr, scheduledAt]() {
		auto player = playerPtr.lock();
		if (!player) {
			logger.debug("Skipping save for player because player is no longer online.");
			return;
		}
		if (m_playerMap[player->getGUID()] != scheduledAt) {
			logger.warn("Skipping save for player because another save has been scheduled.");
			return;
		}
		doSavePlayer(player);
	});
}

bool SaveManager::doSavePlayer(std::shared_ptr<Player> player, std::optional<Position> position) {
	if (!player) {
		logger.debug("Failed to save player because player is null.");
		return false;
	}

	Benchmark bm_savePlayer;
	Player::PlayerLock lock(player);
	m_playerMap.erase(player->getGUID());
	if (g_game().getGameState() == GAME_STATE_NORMAL) {
		logger.debug("Saving player {}.", player->getName());
	}

	bool saveSuccess = IOLoginData::savePlayer(player, position);
	if (!saveSuccess) {
		logger.error("Failed to save player {}.", player->getName());
	}

	auto duration = bm_savePlayer.duration();
	logger.debug("Saving player {} took {} milliseconds.", player->getName(), duration);
	return saveSuccess;
}

bool SaveManager::savePlayer(std::shared_ptr<Player> player, std::optional<Position> position) {
	if (!player) return false;
	if (player->isBotPlayer()) {
		enqueueBot({player->getGUID(), player, position.value_or(player->getLoginPosition())});
		return true; // queued, never an acknowledgement of SQL durability
	}
	if (player->isOnline() && g_game().getGameState() != GAME_STATE_SHUTDOWN) {
		schedulePlayer(player);
		return true;
	}

	return doSavePlayer(player);
}

void SaveManager::saveGuild(std::shared_ptr<Guild> guild) {
	if (!guild) {
		logger.debug("Failed to save guild because guild is null.");
		return;
	}

	Benchmark bm_saveGuild;
	logger.debug("Saving guild {}...", guild->getName());
	IOGuild::saveGuild(guild);

	auto duration = bm_saveGuild.duration();
	logger.debug("Saving guild {} took {} milliseconds.", guild->getName(), duration);
}

void SaveManager::saveMap() {
	Benchmark bm_saveMap;
	logger.debug("Saving map...");
	bool saveSuccess = Map::save();
	if (!saveSuccess) {
		logger.error("Failed to save map.");
	}

	auto duration = bm_saveMap.duration();
	logger.debug("Map saved in {} milliseconds.", duration);
}

void SaveManager::saveKV() {
	Benchmark bm_saveKV;
	logger.debug("Saving key-value store...");
	bool saveSuccess = kv.saveAll();
	if (!saveSuccess) {
		logger.error("Failed to save key-value store.");
	}

	auto duration = bm_saveKV.duration();
	logger.debug("Key-value store saved in {} milliseconds.", duration);
}
