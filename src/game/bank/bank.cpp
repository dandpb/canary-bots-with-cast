/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "game/bank/bank.hpp"

#include "config/configmanager.hpp"
#include "creatures/players/grouping/guild.hpp"
#include "creatures/players/player.hpp"
#include "database/database.hpp"
#include "game/game.hpp"
#include "game/scheduling/dispatcher.hpp"
#include "game/scheduling/save_manager.hpp"
#include "io/iomarket.hpp"
#include "kv/kv.hpp"
#include "lib/metrics/metrics.hpp"

#include <functional>
#include <limits>
#include <optional>
#include <random>
#include <string_view>
#include <unordered_map>

namespace {
	std::mutex pendingGuildsMutex;
	std::unordered_map<uint32_t, std::shared_ptr<Guild>> pendingGuilds;

	struct BankAccount {
		explicit BankAccount(const std::shared_ptr<Bankable> &handle) :
			handle(handle), player(handle->getPlayer()),
			guild(handle->isGuild() ? std::static_pointer_cast<Guild>(handle) : nullptr) { }

		uint32_t id() const { return player ? player->getGUID() : guild->getId(); }
		std::string_view table() const { return player ? "players" : "guilds"; }
		bool online() const { return player ? player->isOnline() : g_game().getGuild(guild->getId()) == guild; }

		std::shared_ptr<Bankable> handle;
		std::shared_ptr<Player> player;
		std::shared_ptr<Guild> guild;
	};

	struct AccountLock {
		explicit AccountLock(const BankAccount &account) {
			if (account.player) player.emplace(account.player);
			else guild = account.guild->tryLockBankBalance();
		}

		bool acquired() const { return player.has_value() || guild.owns_lock(); }

		std::optional<Player::PlayerLock> player;
		std::unique_lock<std::mutex> guild;
	};

	void setTransferPending(const BankAccount &account, bool pending) {
		if (account.player) {
			// Player saves and login already honor this settlement fence.
			IOMarket::setPlayerFillPending(account.id(), pending);
			return;
		}
		std::lock_guard lock(pendingGuildsMutex);
		if (pending) pendingGuilds.emplace(account.id(), account.guild);
		else pendingGuilds.erase(account.id());
	}

	void publishTransfer(const BankAccount &from, const BankAccount &to, uint64_t sourceBalance, uint64_t destinationBalance, uint64_t amount) {
		from.handle->setBankBalance(sourceBalance);
		to.handle->setBankBalance(destinationBalance);
		if (from.player) {
			g_metrics().addCounter("balance_decrease", amount, { { "player", from.player->getName() }, { "context", "bank_transfer" } });
		}
		if (to.player) {
			g_metrics().addCounter("balance_increase", amount, { { "player", to.player->getName() }, { "context", "bank_transfer" } });
		}
	}

	void resolveTransfer(std::string receiptKey, std::string receiptToken, std::function<bool(bool)> finish) {
		g_dispatcher().scheduleEvent(1000, [key = std::move(receiptKey), token = std::move(receiptToken), finish = std::move(finish)]() mutable {
			bool committed = false;
			const bool inspected = DBTransaction::executeWithinTransaction([&] {
				auto &db = g_database();
				bool readSucceeded = false;
				const auto row = db.storeQuery(fmt::format(
					"SELECT `value` FROM `server_config` WHERE `config` = {} FOR UPDATE", db.escapeString(key)), readSucceeded);
				committed = row && row->getString("value") == token;
				return readSucceeded;
			});
			if (!inspected || !finish(committed)) {
				resolveTransfer(std::move(key), std::move(token), std::move(finish));
			}
		}, "Bank::resolveTransfer");
	}
}

Bank::Bank(const std::shared_ptr<Bankable> &bankable) :
	m_bankable(bankable) {
}

Bank::~Bank() {
	auto bankable = getBankable();
	if (!m_dirty || bankable == nullptr || bankable->isOnline() || hasPendingTransfer()) {
		return;
	}
	const auto &player = bankable->getPlayer();
	if (player && !player->isOnline()) {
		g_saveManager().savePlayer(player);

		return;
	}
	if (bankable->isGuild()) {
		const auto guild = static_self_cast<Guild>(bankable);
		if (guild && !guild->isOnline()) {
			g_saveManager().saveGuild(guild);
		}
	}
}

bool Bank::credit(uint64_t amount) {
	return balance(balance() + amount);
}

bool Bank::debit(uint64_t amount) {
	if (!hasBalance(amount)) {
		return false;
	}
	return balance(balance() - amount);
}

bool Bank::balance(uint64_t amount) const {
	auto bankable = getBankable();
	if (!bankable || hasPendingTransfer()) {
		return false;
	}
	bankable->setBankBalance(amount);
	m_dirty = true;
	return true;
}

uint64_t Bank::balance() {
	auto bankable = getBankable();
	if (!bankable) {
		return 0;
	}
	return bankable->getBankBalance();
}

bool Bank::hasBalance(const uint64_t amount) {
	return balance() >= amount;
}

std::shared_ptr<Guild> Bank::getPendingGuildTransfer(uint32_t guildId) {
	std::lock_guard lock(pendingGuildsMutex);
	const auto it = pendingGuilds.find(guildId);
	return it == pendingGuilds.end() ? nullptr : it->second;
}

bool Bank::hasPendingTransfer() const {
	const auto &bankable = getBankable();
	if (!bankable) return false;
	const BankAccount account(bankable);
	if (account.player) return IOMarket::playerHasPendingFill(account.id());
	return account.guild && getPendingGuildTransfer(account.id());
}

const std::set<std::string> deniedNames = {
	"accountmanager",
	"rooksample",
	"druidsample",
	"sorcerersample",
	"knightsample",
	"paladinsample"
};

bool Bank::transferTo(const std::shared_ptr<Bank> &destination, uint64_t amount, bool *pending) {
	if (pending) *pending = false;
	if (!destination) {
		g_logger().error("Bank::transferTo: destination is nullptr");
		return false;
	}

	const auto bankable = getBankable();
	if (!bankable) {
		g_logger().error("Bank::transferTo: bankable is nullptr");
		return false;
	}

	const auto destinationBankable = destination->getBankable();
	if (!destinationBankable) {
		g_logger().error("Bank::transferTo: destinationBankable is nullptr");
		return false;
	}

	const BankAccount from(bankable);
	const BankAccount to(destinationBankable);
	if ((!from.player && !from.guild) || (!to.player && !to.guild) || !from.id() || !to.id()) {
		return false;
	}
	const auto &destinationPlayer = to.player;
	const auto &bankablePlayer = from.player;

	if (destinationPlayer && bankablePlayer) {
		auto name = asLowerCaseString(destinationPlayer->getName());
		replaceString(name, " ", "");

		if (deniedNames.contains(name)) {
			g_logger().warn("Bank::transferTo: denied name: {}", name);
			return false;
		}

		const auto destinationTownId = destinationPlayer->getTown()->getID();
		const auto bankableTownId = bankablePlayer->getTown()->getID();
		const auto minTownIdToTransferFromMain = g_configManager().getNumber(MIN_TOWN_ID_TO_BANK_TRANSFER_FROM_MAIN);

		if (destinationTownId < minTownIdToTransferFromMain && bankableTownId >= minTownIdToTransferFromMain) {
			g_logger().warn("[{}] Player {} is from main town, trying to transfer money to player {} in {} town.", __FUNCTION__, bankablePlayer->getName(), destinationPlayer->getName(), destinationTownId);
			return false;
		}

		if (bankableTownId < minTownIdToTransferFromMain && destinationTownId >= minTownIdToTransferFromMain) {
			g_logger().warn("[{}] Player {} is not from main town, trying to transfer money to player {} in {} town.", __FUNCTION__, bankablePlayer->getName(), destinationPlayer->getName(), destinationTownId);
			return false;
		}
	}

	if (hasPendingTransfer() || destination->hasPendingTransfer()) {
		if (pending) *pending = true;
		return false;
	}

	const auto fromIdentity = std::pair{from.table(), from.id()};
	const auto toIdentity = std::pair{to.table(), to.id()};
	if (fromIdentity == toIdentity || amount == 0) return hasBalance(amount);

	const bool fromFirst = fromIdentity < toIdentity;
	const auto receiptKey = fmt::format("bank:transfer:{}:{}", from.table(), from.id());
	const auto receiptToken = fmt::format("{}-{:08x}", KV::generateUUID(), std::random_device{}());
	const bool sourceLive = from.online() || m_dirty;
	const bool destinationLive = to.online() || destination->m_dirty;
	uint64_t sourceBalance = 0;
	uint64_t destinationBalance = 0;
	bool written = false;
	{
		const AccountLock first(fromFirst ? from : to);
		if (!first.acquired()) return false;
		const AccountLock second(fromFirst ? to : from);
		if (!second.acquired()) return false;

		const DBTransaction::ScopedReceipt receipt(receiptKey, receiptToken);
		const auto outcome = DBTransaction::executeWithOutcome([&] {
			auto &db = g_database();
			const auto lockBalance = [&](const BankAccount &account, bool live) -> std::optional<uint64_t> {
				const auto row = db.storeQuery(fmt::format(
					"SELECT `balance` FROM `{}` WHERE `id` = {} FOR UPDATE", account.table(), account.id()));
				if (!row) return std::nullopt;
				return live ? account.handle->getBankBalance() : row->getNumber<uint64_t>("balance");
			};
			const auto firstBalance = lockBalance(fromFirst ? from : to, fromFirst ? sourceLive : destinationLive);
			const auto secondBalance = lockBalance(fromFirst ? to : from, fromFirst ? destinationLive : sourceLive);
			if (!firstBalance || !secondBalance) return false;
			const auto debitBalance = fromFirst ? *firstBalance : *secondBalance;
			const auto creditBalance = fromFirst ? *secondBalance : *firstBalance;
			if (debitBalance < amount || creditBalance > std::numeric_limits<uint64_t>::max() - amount) return false;

			sourceBalance = debitBalance - amount;
			destinationBalance = creditBalance + amount;
			const auto writeBalance = [&](const BankAccount &account, uint64_t balance) {
				return db.executeQuery(fmt::format("UPDATE `{}` SET `balance` = {} WHERE `id` = {}", account.table(), balance, account.id()));
			};
			written = writeBalance(from, sourceBalance) && writeBalance(to, destinationBalance);
			return written;
		});
		if (outcome == DBTransaction::Outcome::Committed) {
			if (!written) return false;
			publishTransfer(from, to, sourceBalance, destinationBalance, amount);
			m_dirty = false;
			destination->m_dirty = false;
			return true;
		}
		if (outcome != DBTransaction::Outcome::Uncertain) return false;

		setTransferPending(from, true);
		setTransferPending(to, true);
	}

	if (pending) *pending = true;
	g_logger().error("BANK_TRANSFER_UNCERTAIN receipt={}", receiptKey);
	const auto disconnectPending = [](const std::shared_ptr<Player> &player) {
		if (!player || !player->isOnline()) return;
		player->sendTextMessage(MESSAGE_EVENT_ADVANCE, "The bank is reconciling a transfer. Check your balance before retrying.");
		player->removePlayer(true);
	};
	disconnectPending(from.player);
	disconnectPending(to.player);
	resolveTransfer(receiptKey, receiptToken, [from, to, amount, sourceBalance, destinationBalance, sourceLive, destinationLive](bool committed) {
		if (committed) {
			// Preserve credits staged by logout after an unknown COMMIT.
			const auto debitBalance = sourceLive && from.player ? from.handle->getBankBalance() : sourceBalance + amount;
			const auto creditBalance = destinationLive && to.player ? to.handle->getBankBalance() : destinationBalance - amount;
			if (debitBalance < amount || creditBalance > std::numeric_limits<uint64_t>::max() - amount) return false;
			publishTransfer(from, to, debitBalance - amount, creditBalance + amount, amount);
		}
		setTransferPending(from, false);
		setTransferPending(to, false);
		return true;
	});
	return false;
}

bool Bank::withdraw(const std::shared_ptr<Player> &player, uint64_t amount) {
	if (!player) {
		return false;
	}
	if (!debit(amount)) {
		return false;
	}
	g_game().addMoney(player, amount);
	g_metrics().addCounter("balance_decrease", amount, { { "player", player->getName() }, { "context", "bank_withdraw" } });
	return true;
}

bool Bank::deposit(const std::shared_ptr<Bank> &destination) {
	auto bankable = getBankable();
	if (!bankable) {
		return false;
	}
	auto player = bankable->getPlayer();
	if (!player) {
		return false;
	}
	auto amount = player->getMoney();
	return deposit(destination, amount);
}

bool Bank::deposit(const std::shared_ptr<Bank> &destination, uint64_t amount) {
	if (!destination || destination->hasPendingTransfer()) {
		return false;
	}
	auto bankable = getBankable();
	if (!bankable) {
		return false;
	}
	const auto &player = bankable->getPlayer();
	if (!player) {
		return false;
	}
	if (!g_game().removeMoney(player, amount)) {
		return false;
	}
	g_metrics().addCounter("balance_decrease", amount, { { "player", player->getName() }, { "context", "bank_deposit" } });
	return destination->credit(amount);
}
