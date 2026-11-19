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
#include "io/iomapserialize.hpp"
#include "io/iomarket.hpp"
#include "kv/kv.hpp"
#include "lib/di/container.hpp"
#include "creatures/players/player.hpp"
#include "utils/tools.hpp"
#include "game/scheduling/dispatcher.hpp"

#include <algorithm>
#include <random>

namespace {
std::string saveReceiptToken() {
	return fmt::format("{}-{:08x}", KV::generateUUID(), std::random_device{}());
}
}

void checkpointBotReloadPlayers(const BotReloadSnapshot& snapshot) {
	for (const auto& entry : snapshot.entries) {
		if (entry.player) g_saveManager().savePlayer(entry.player, entry.position);
	}
}

std::shared_ptr<Player> SaveManager::getPendingBotPlayer(uint32_t guid) const {
	auto pending = playerSaves_.find(guid);
	return pending && pending->player && pending->player->isBotPlayer() ? pending->player : nullptr;
}

std::shared_ptr<Player> SaveManager::getPendingBotPlayer(const std::string &name) const {
	const auto normalized = asLowerCaseString(name);
	for (const auto& pending : playerSaves_.snapshot()) {
		if (pending.player && pending.player->isBotPlayer() && asLowerCaseString(pending.player->getName()) == normalized) return pending.player;
	}
	return nullptr;
}

bool SaveManager::hasPendingLogout(uint32_t guid) const {
	const auto pending = playerSaves_.find(guid);
	return pending && pending->logout;
}

bool SaveManager::hasPendingLogout(const std::string &name) const {
	const auto normalized = asLowerCaseString(name);
	return std::ranges::any_of(playerSaves_.snapshot(), [&](const auto &pending) {
		return pending.logout && asLowerCaseString(pending.player->getName()) == normalized;
	});
}

SaveManager::SaveManager(ThreadPool &threadPool, KVStore &kvStore, Logger &logger, Game &game) :
	threadPool(threadPool), kv(kvStore), logger(logger), game(game) { }

SaveManager &SaveManager::getInstance() {
	return inject<SaveManager>();
}

SaveManager::SaveBatch SaveManager::captureBatch() {
	Benchmark captureTimer;
	SaveBatch batch;
	batch.final = finalSaving_;
	// Capture strong references and position policy on the dispatcher, before any SQL.
	std::unordered_map<uint32_t, PlayerSave> captured;
	if (batch.final) {
		captured = finalPlayers_;
	} else {
		for (const auto& [_, player] : game.getPlayers()) {
			captured[player->getGUID()] = {player->getGUID(), player, player->getPosition()};
		}
		if (auto* engine = getBotEngineIfLoaded()) {
			for (const auto& snapshot : engine->capturePersistentPlayers()) {
				const auto guid = snapshot.player->getGUID();
				captured[guid] = {guid, snapshot.player, snapshot.loginPosition};
			}
		}
		for (const auto& pending : playerSaves_.snapshot()) captured.try_emplace(pending.guid, pending);
	}
	for (const auto& [guid, save] : captured) {
		if (batch.final || save.logout || !save.player || save.player->isBotPlayer()) {
			batch.players.emplace_back(enqueuePlayerSave(save), save.player ? save.player->getName() : std::to_string(guid));
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

bool SaveManager::saveBatch(SaveBatch batch, const std::function<bool()> &saveMotd) {
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
	if (batch.final) {
		// Checkpoints deferred by settlement can still contribute to global KV on retry.
		if (!failures && !finalCommitUncertain_) {
			const bool saved = saveFinalStage("motd", [&] { return DBTransaction::executeWithinTransaction(saveMotd); })
				&& saveFinalStage("guilds", [&] {
					return DBTransaction::executeWithinTransaction([&] {
						return std::ranges::all_of(batch.guilds, [this](const auto &guild) { return saveGuild(guild); });
					});
				})
				&& saveMap(true)
				&& saveKV(true);
			failures += !saved;
		}
	} else {
		if (finalSaving_) return false;
		for (const auto& guild : batch.guilds) failures += !saveGuild(guild);
		failures += !saveMap(false);
		failures += !saveKV(false);
	}
	if (batch.final && finalCommitUncertain_) return false;
	if (failures) logger.error("Server save completed with {} failed writes", failures);
	else logger.info("Server saved {} players in {} milliseconds", batch.players.size(), timer.duration());
	return failures == 0;
}

void SaveManager::saveAll() {
	if (!finalSaving_) saveBatch(captureBatch());
}

void SaveManager::beginFinalSave() {
	finalSaving_ = true;
	finalSaveToken_ = saveReceiptToken();
	for (auto& entry : playerSaves_.snapshot()) finalPlayers_.emplace(entry.guid, std::move(entry));
	if (auto* engine = getBotEngineIfLoaded()) {
		for (const auto& entry : engine->capturePersistentPlayers()) {
			const auto guid = entry.player->getGUID();
			finalPlayers_[guid] = {guid, entry.player, entry.loginPosition};
		}
	}
	for (const auto& [_, player] : game.getPlayers()) {
		finalPlayers_[player->getGUID()] = {player->getGUID(), player, player->getPosition()};
	}
}

bool SaveManager::saveFinal(const std::function<bool()> &saveMotd) {
	// Stable receipts fence retries of the same shutdown at the database.
	finalCommitUncertain_ = false;
	for (auto& [_, save] : finalPlayers_) {
		if (save.receipt.empty()) save.receipt = finalSaveToken_;
		if (save.player && !save.checkpoint) {
			Player::PlayerLock lock(save.player);
			captureCheckpoint(save);
		}
	}
	if (saveBatch(captureBatch(), saveMotd) && !finalCommitUncertain_) {
		finalPlayers_.clear();
		return true;
	}
	return false;
}

bool SaveManager::saveFinalStage(const std::string &stage, const std::function<bool()> &save) {
	DBTransaction::ScopedReceipt receipt("save:final:" + stage, finalSaveToken_);
	DBTransaction::clearOutcome();
	const bool saved = save();
	observeFinalOutcome();
	return saved;
}

void SaveManager::observeFinalOutcome() {
	if (finalSaving_ && DBTransaction::lastOutcome() == DBTransaction::Outcome::Uncertain) {
		finalCommitUncertain_ = true;
	}
}

void SaveManager::scheduleAll() {
	if (finalSaving_) return;
	// Dependencies are queued before the batch waiter on the FIFO worker pool.
	// Neither the waiter nor a save worker consults the unloadable bot engine.
	auto batch = captureBatch();
	if (!g_configManager().getBoolean(TOGGLE_SAVE_ASYNC)) { saveBatch(std::move(batch)); return; }
	threadPool.detach_task([this, batch = std::move(batch)]() mutable { saveBatch(std::move(batch)); });
}

void SaveManager::captureCheckpoint(PlayerSave &save) {
	// This runs on the dispatcher before any reactivation can mutate the object.
	if (save.player && !save.checkpoint && !IOMarket::playerHasPendingFill(save.guid)) {
		try {
			save.checkpoint = std::make_shared<const PlayerSaveSnapshot>(IOLoginData::capturePlayerSave(save.player, save.position));
		} catch (const std::exception& error) {
			logger.error("Could not capture player {} checkpoint: {}", save.guid, error.what());
		}
	}
}

std::shared_future<bool> SaveManager::enqueuePlayerSave(PlayerSave save) {
	const auto player = save.player;
	std::optional<Player::PlayerLock> lock;
	if (player && !save.checkpoint && !save.receipt.empty()) lock.emplace(player);
	captureCheckpoint(save);
	const auto guid = save.guid;
	auto requested = playerSaves_.request(guid, std::move(save));
	if (requested.start) playerSavePool_.detach_task([this, guid] { runPlayerSave(guid); });
	return requested.completed;
}

void SaveManager::runPlayerSave(uint32_t guid) {
	// Keep a transaction off the dispatcher's main DB connection. TLS belongs
	// to the executable and cannot retain an unloaded engine's code.
	thread_local std::unique_ptr<Database> connection;
	while (auto work = playerSaves_.take(guid)) {
		if (work->value.player && work->value.player->isPersistenceDiscarded()) {
			if (playerSaves_.finish(guid, work->generation, true)) continue;
			break;
		}
		bool success = false;
		try {
			if (!connection) {
				auto candidate = std::make_unique<Database>();
				if (!candidate->connect()) throw std::runtime_error("save DB connection unavailable");
				connection = std::move(candidate);
			}
			Database::ScopedConnection route(*connection);
			if (work->value.player && !work->value.checkpoint) throw std::runtime_error("player checkpoint unavailable");
			if (work->value.checkpoint) {
				if (IOMarket::playerHasPendingFill(guid)) throw std::runtime_error("market settlement is awaiting reconciliation");
				std::optional<DBTransaction::ScopedReceipt> receipt;
				if (!work->value.receipt.empty()) receipt.emplace(fmt::format("save:player:{}", guid), work->value.receipt);
				success = IOLoginData::persistPlayerSave(*work->value.checkpoint);
				observeFinalOutcome();
				if (success) threadPool.detach_task([player = work->value.player, snapshot = work->value.checkpoint] {
					// Dispatcher has slots for its general pool, not these dedicated SQL
					// workers. Relay only the tiny acknowledgement through a known producer;
					// never move SQL or mutable character serialization back into that pool.
					g_dispatcher().addEvent([player, snapshot] {
						IOLoginData::acknowledgePlayerSave(player, *snapshot);
					}, "SaveManager::acknowledgeCheckpoint");
				});
			}
			else {
				const auto& pos = work->value.position;
				const auto savePosition = [&] {
					return g_database().executeQuery(fmt::format(
						"UPDATE `players` SET `posx`={}, `posy`={}, `posz`={} WHERE `id`={}", pos.x, pos.y, pos.z, guid));
				};
				if (work->value.receipt.empty()) {
					success = savePosition();
				} else {
					DBTransaction::ScopedReceipt receipt(fmt::format("save:player:{}", guid), work->value.receipt);
					success = DBTransaction::executeWithinTransaction(savePosition);
					observeFinalOutcome();
				}
			}
		} catch (const std::exception& error) {
			logger.error("Player checkpoint failed for {}: {}", guid, error.what());
		} catch (...) { logger.error("Player checkpoint failed for {} with an unknown exception", guid); }
		if (playerSaves_.finish(guid, work->generation, success)) continue;
		if (!success && work->value.logout && !finalSaving_) {
			threadPool.detach_task([this, guid, receipt = work->value.receipt] {
				g_dispatcher().scheduleEvent(2000, [this, guid, receipt] {
					if (finalSaving_) return;
					const auto pending = playerSaves_.find(guid);
					if (pending && pending->receipt == receipt) enqueuePlayerSave(*pending);
				}, "SaveManager::retryLogout");
			});
		}
		break;
	}
}

void SaveManager::saveBotPosition(uint32_t guid, const Position& position) {
	if (finalSaving_) return;
	// Dispatcher only. Preserve a pending full character save when updating position.
	enqueuePlayerSave({guid, getPendingBotPlayer(guid), position});
}

void SaveManager::schedulePlayer(std::weak_ptr<Player> playerPtr) {
	if (finalSaving_) return;
	auto playerToSave = playerPtr.lock();
	if (!playerToSave) {
		logger.debug("Skipping save for player because player is no longer online.");
		return;
	}

	if (playerToSave->isBotPlayer()) {
		enqueuePlayerSave({playerToSave->getGUID(), playerToSave, playerToSave->getLoginPosition()});
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
	const auto guid = playerToSave->getGUID();
	uint64_t ticket;
	{
		std::lock_guard lock(saveTicketsMutex_);
		ticket = ++nextSaveTicket_;
		saveTickets_[guid] = ticket;
	}
	threadPool.detach_task([this, playerPtr, guid, ticket]() {
		auto player = playerPtr.lock();
		if (!player) {
			consumeSaveTicket(guid, ticket);
			logger.debug("Skipping save for player because player is no longer online.");
			return;
		}
		doSavePlayer(player, ticket);
	});
}

bool SaveManager::consumeSaveTicket(uint32_t guid, uint64_t ticket) {
	std::lock_guard lock(saveTicketsMutex_);
	const auto pending = saveTickets_.find(guid);
	if (pending == saveTickets_.end() || pending->second != ticket) return false;
	saveTickets_.erase(pending);
	return true;
}

bool SaveManager::doSavePlayer(std::shared_ptr<Player> player, std::optional<uint64_t> ticket) {
	if (!player) {
		logger.debug("Failed to save player because player is null.");
		return false;
	}

	Benchmark bm_savePlayer;
	Player::PlayerLock lock(player);
	if (ticket && !consumeSaveTicket(player->getGUID(), *ticket)) return false;
	if (player->isPersistenceDiscarded() || finalSaving_ || hasPendingLogout(player->getGUID()) || IOMarket::playerHasPendingFill(player->getGUID())) return false;
	if (g_game().getGameState() == GAME_STATE_NORMAL) {
		logger.debug("Saving player {}.", player->getName());
	}

	bool saveSuccess = IOLoginData::savePlayer(player);
	observeFinalOutcome();
	if (!saveSuccess) {
		logger.error("Failed to save player {}.", player->getName());
	}

	auto duration = bm_savePlayer.duration();
	logger.debug("Saving player {} took {} milliseconds.", player->getName(), duration);
	return saveSuccess;
}

bool SaveManager::savePlayer(std::shared_ptr<Player> player, std::optional<Position> position) {
	if (!player || player->isPersistenceDiscarded()) return false;
	if (finalSaving_) return true; // Owned by the final batch.
	if (player->isBotPlayer()) {
		enqueuePlayerSave({player->getGUID(), player, position.value_or(player->getLoginPosition())});
		return true; // queued, never an acknowledgement of SQL durability
	}
	if (player->isOnline() && g_game().getGameState() != GAME_STATE_SHUTDOWN) {
		schedulePlayer(player);
		return true;
	}

	return doSavePlayer(player);
}

void SaveManager::saveLogoutPlayer(const std::shared_ptr<Player> &player) {
	if (player->isPersistenceDiscarded()) return;
	PlayerSave save {player->getGUID(), player, player->getLoginPosition()};
	save.logout = !player->isBotPlayer();
	if (finalSaving_) {
		finalPlayers_[save.guid] = std::move(save);
		return;
	}
	if (save.logout) save.receipt = saveReceiptToken();
	enqueuePlayerSave(std::move(save));
}

bool SaveManager::saveGuild(std::shared_ptr<Guild> guild) {
	if (!guild) {
		logger.debug("Failed to save guild because guild is null.");
		return false;
	}

	Benchmark bm_saveGuild;
	logger.debug("Saving guild {}...", guild->getName());
	const bool saved = IOGuild::saveGuild(guild);

	auto duration = bm_saveGuild.duration();
	logger.debug("Saving guild {} took {} milliseconds.", guild->getName(), duration);
	return saved;
}

bool SaveManager::saveMap(bool final) {
	Benchmark bm_saveMap;
	logger.debug("Saving map...");
	const bool saveSuccess = final
		? saveFinalStage("house-info", IOMapSerialize::saveHouseInfo) && saveFinalStage("house-items", IOMapSerialize::saveHouseItems)
		: Map::save();
	if (!saveSuccess) {
		logger.error("Failed to save map.");
	}

	auto duration = bm_saveMap.duration();
	logger.debug("Map saved in {} milliseconds.", duration);
	return saveSuccess;
}

bool SaveManager::saveKV(bool final) {
	Benchmark bm_saveKV;
	logger.debug("Saving key-value store...");
	const bool saveSuccess = final ? saveFinalStage("kv", [this] { return kv.saveAll(); }) : kv.saveAll();
	if (!saveSuccess) {
		logger.error("Failed to save key-value store.");
	}

	auto duration = bm_saveKV.duration();
	logger.debug("Key-value store saved in {} milliseconds.", duration);
	return saveSuccess;
}
