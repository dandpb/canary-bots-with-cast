#include "io/iostoreorders.hpp"

#include "account/account.hpp"
#include "account/account_repository.hpp"
#include "creatures/players/player.hpp"
#include "database/database.hpp"
#include "enums/account_coins.hpp"
#include "game/game.hpp"
#include "io/iologindata.hpp"
#include "kv/kv.hpp"

#include <limits>

namespace {
	using IOStoreOrders::Order;
	using Outcome = DBTransaction::Outcome;

	CoinType walletType(bool transferable) {
		return transferable ? CoinType::Transferable : CoinType::Normal;
	}

	std::optional<uint32_t> lockWallet(Database &database, uint32_t accountId, bool transferable) {
		const auto column = transferable ? "coins_transferable" : "coins";
		const auto row = database.storeQuery(fmt::format("SELECT `{}` FROM `accounts` WHERE `id` = {} FOR UPDATE", column, accountId));
		if (!row) {
			return std::nullopt;
		}
		return row->getNumber<uint32_t>(column);
	}

	bool canSaveCharacter(Database &database, uint32_t playerGuid, uint32_t accountId, bool lock) {
		return database.storeQuery(fmt::format(
			"SELECT `id` FROM `players` WHERE `id` = {} AND `account_id` = {} AND `save` <> 0{}",
			playerGuid, accountId, lock ? " FOR UPDATE" : ""
		)) != nullptr;
	}

	std::optional<Order> readOrder(Database &database, uint64_t id, bool lock) {
		const auto row = database.storeQuery(fmt::format(
			"SELECT `id`, `player_guid`, `account_id`, `offer_id`, `transferable`, `amount`, `detail`, `state` "
			"FROM `store_orders` WHERE `id` = {}{}", id, lock ? " FOR UPDATE" : ""
		));
		if (!row) {
			return std::nullopt;
		}
		return Order {
			row->getNumber<uint64_t>("id"),
			row->getNumber<uint32_t>("player_guid"),
			row->getNumber<uint32_t>("account_id"),
			row->getNumber<uint32_t>("offer_id"),
			row->getNumber<uint8_t>("transferable") != 0,
			row->getNumber<uint32_t>("amount"),
			row->getString("detail"),
			row->getString("state"),
		};
	}

	// The caller holds the order row lock and has checked the previous state.
	bool changeState(Database &database, uint64_t id, const char* state) {
		return database.executeQuery(fmt::format("UPDATE `store_orders` SET `state` = '{}' WHERE `id` = {}", state, id));
	}
}

IOStoreOrders::Reservation IOStoreOrders::reserve(uint32_t playerGuid, uint32_t accountId, uint32_t offerId, bool transferable, uint32_t amount, const std::string &detail) {
	if (playerGuid == 0 || accountId == 0 || offerId == 0 || detail.empty() || detail.size() > 255 || detail.find('\0') != std::string::npos) {
		return {};
	}
	auto &database = g_database();
	uint64_t activeId = 0;
	uint64_t createdId = 0;
	const auto outcome = DBTransaction::executeWithOutcome([&] {
		// Reserve and refund both take the account row before the order row.
		const auto balance = lockWallet(database, accountId, transferable);
		if (!balance) {
			return false;
		}
		bool searched = false;
		const auto active = database.storeQuery(fmt::format(
			"SELECT `id` FROM `store_orders` WHERE `active_account_id` = {} FOR UPDATE", accountId
		), searched);
		if (!searched || !canSaveCharacter(database, playerGuid, accountId, true)) {
			return false;
		}
		if (active) {
			activeId = active->getNumber<uint64_t>("id");
			return false;
		}
		if (*balance < amount) {
			return false;
		}
		if (amount != 0) {
			const auto coinType = walletType(transferable);
			auto &accounts = g_accountRepository();
			if (!accounts.setCoins(accountId, coinType, *balance - amount)
				|| !accounts.registerCoinsTransaction(accountId, CoinTransactionType::Remove, amount, coinType, detail)) {
				return false;
			}
		}
		if (!database.executeQuery(fmt::format(
				"INSERT INTO `store_orders` (`player_guid`, `account_id`, `offer_id`, `transferable`, `amount`, `detail`) "
				"VALUES ({}, {}, {}, {}, {}, {})",
				playerGuid, accountId, offerId, static_cast<int>(transferable), amount, database.escapeString(detail)
			))) {
			return false;
		}
		createdId = database.getLastInsertId();
		return createdId != 0;
	});
	if (outcome == Outcome::Committed && createdId != 0) {
		return { createdId, "reserved" };
	}
	if (outcome == Outcome::Uncertain) {
		return { createdId, "uncertain" };
	}
	return activeId != 0 ? Reservation { activeId, "pending" } : Reservation {};
}

std::optional<Order> IOStoreOrders::get(uint64_t id) {
	if (id == 0) {
		return std::nullopt;
	}
	return readOrder(g_database(), id, false);
}

bool IOStoreOrders::claim(uint64_t id, uint32_t playerGuid) {
	if (id == 0 || playerGuid == 0) {
		return false;
	}
	auto &database = g_database();
	return DBTransaction::executeWithinTransaction([&] {
		const auto order = readOrder(database, id, true);
		return order && order->playerGuid == playerGuid && order->state == "reserved"
			&& canSaveCharacter(database, playerGuid, order->accountId, true) && changeState(database, id, "delivering");
	});
}

bool IOStoreOrders::finish(uint64_t id, uint32_t playerGuid) {
	const auto order = get(id);
	if (!order || order->playerGuid != playerGuid) {
		return false;
	}
	if (order->state == "complete") {
		return true;
	}
	const auto player = g_game().getPlayerByGUID(playerGuid);
	if (order->state != "delivering" || !player) {
		return false;
	}
	const Player::PlayerLock playerLock(player);
	const auto account = player->getAccount();
	auto &database = g_database();
	if (!player->isOnline() || !account || account->getID() != order->accountId
		|| !canSaveCharacter(database, playerGuid, order->accountId, false)
		|| !IOLoginData::savePlayer(player, player->getPosition()) || !g_kv().saveAll()) {
		return false;
	}
	return DBTransaction::executeWithinTransaction([&] {
		const auto current = readOrder(database, id, true);
		return current && (current->state == "complete" || (current->state == "delivering"
			&& canSaveCharacter(database, playerGuid, order->accountId, true) && changeState(database, id, "complete")));
	});
}

const char* IOStoreOrders::resolve(uint64_t id, bool refund) {
	auto &database = g_database();
	const auto original = get(id);
	if (!original) {
		return "refused";
	}
	const auto terminalState = refund ? "refunded" : "complete";
	if (original->state == terminalState) {
		return terminalState;
	}
	const auto outcome = DBTransaction::executeWithOutcome([&] {
		std::optional<uint32_t> balance;
		if (refund && original->amount != 0) {
			balance = lockWallet(database, original->accountId, original->transferable);
			if (!balance) {
				return false;
			}
		}
		const auto order = readOrder(database, id, true);
		if (!order) {
			return false;
		}
		if (order->state == terminalState) {
			return true;
		}
		if (order->state != "delivering" && !(refund && order->state == "reserved")) {
			return false;
		}
		if (balance) {
			if (order->amount > std::numeric_limits<uint32_t>::max() - *balance) {
				return false;
			}
			const auto coinType = walletType(order->transferable);
			const auto detail = fmt::format("Store refund {}: {}", order->id, order->detail);
			auto &accounts = g_accountRepository();
			if (!accounts.setCoins(order->accountId, coinType, *balance + order->amount)
				|| !accounts.registerCoinsTransaction(order->accountId, CoinTransactionType::Add, order->amount, coinType, detail)) {
				return false;
			}
		}
		return changeState(database, id, terminalState);
	});
	if (outcome == Outcome::Uncertain) {
		return "uncertain";
	}
	return outcome == Outcome::Committed ? terminalState : "refused";
}
