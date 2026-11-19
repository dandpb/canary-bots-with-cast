/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

// Bot market wrapper functions.
//
// Mirrors the inner transaction work of:
//   - Game::playerCreateMarketOffer    (game.cpp:9398)
//   - Game::playerAcceptMarketOffer    (game.cpp:9588)
//   - Game::playerCancelMarketOffer    (game.cpp:9500)
//
// Key differences from the user-facing functions:
//   - Skip isInMarket / isUIExhausted gates (bots have no UI session).
//   - Skip account-self-match check (bot scheduler filters bot-bot pairs at SQL level).
//   - Skip depotLocker requirement; bot SELL/BUY-fulfill bypasses depot item removal
//     (items are conjured for delivery to the real-player counterparty).
//   - Skip UI side-effects (sendMarketEnter, sendMarketBrowseItem, sendMarketAcceptOffer,
//     sendMarketCancelOffer, sendCancelMessage, sendTextMessage, onReceiveMail).
//
// Preserved (so real players experience identical economic side-effects):
//   - Standard 2% fee on offer creation (clamped 20-1M gp).
//   - Bank balance debit/credit for both bot and counterparty.
//   - Item delivery to the real-player counterparty's inbox via the same
//     addItemBatchToPaginedContainer primitive used by processItemInsertion.
//   - IOMarket::createOffer / acceptOffer / deleteOffer / appendHistory /
//     writeClose for canonical DB writes.
//   - g_saveManager().savePlayer() for offline counterparties.
//
// IMPORTANT: when the user-facing market functions in game.cpp change, mirror those
// changes here. The two paths share no helper code; drift is the main risk.

#include "game/game.hpp"

#include "account/account.hpp"
#include "account/account_repository.hpp"
#include "config/configmanager.hpp"
#include "creatures/players/player.hpp"
#include "database/botdatabasetasks.hpp" // bundle 6: dedicated bot-DB worker
#include "enums/account_coins.hpp"
#include "enums/account_errors.hpp"
#include "game/scheduling/save_manager.hpp"
#include "game/scheduling/dispatcher.hpp"
#include "io/functions/iologindata_save_player.hpp"
#include "io/iologindata.hpp"
#include "io/iomarket.hpp"
#include "items/containers/depot/depotchest.hpp"
#include "items/containers/inbox/inbox.hpp"
#include "items/items.hpp"
#include "lib/metrics/metrics.hpp"
#include "lua/scripts/lua_environment.hpp"

#include <algorithm>
#include <limits>

bool Game::botCreateMarketOffer(uint32_t botGuid, uint8_t action, uint16_t itemId, uint16_t amount, uint64_t price, uint8_t tier, bool anonymous) {
	if (getGameState() == GAME_STATE_SHUTDOWN) return false;
	// JITTER FIX 2026-06-11 (bundle 3): this function used to perform THREE
	// synchronous DB operations on the dispatcher per offer — a full offline
	// IOLoginData load for hibernated bots (getPlayerByGUID(.., true)), a sync
	// per-player COUNT (IOMarket::getPlayerOfferCount) and a sync INSERT
	// (IOMarket::createOffer). Behind worker-side DB convoys each INSERT measured
	// 106-151ms; six in one seller fire stacked into an 885ms GlobalEvents task ->
	// HB_STALL 882ms -> the 08:39:28 lagmark. Now:
	//   - validation stays in-memory;
	//   - NO offline load: for hibernated bots the fee/escrow debit was theater
	//     anyway (debited onto a temp Player and discarded — see the 2026-05-27
	//     skip-bot-save precedent below), so it is skipped when the bot is not in
	//     the online map;
	//   - cap check + INSERT collapse into ONE statement enqueued on the
	//     DatabaseTasks worker; the per-player cap is enforced atomically in SQL
	//     (INSERT .. SELECT .. WHERE count < cap; the derived table sidesteps
	//     MySQL error 1093 on self-referencing inserts).
	const ItemType &it = Item::items[itemId];
	if (it.id == 0 || it.wareId == 0) {
		g_logger().warn("[botCreateMarketOffer] item {} not marketable (wareId=0)", itemId);
		return false;
	}

	if (action != MARKETACTION_BUY && action != MARKETACTION_SELL) {
		return false;
	}

	if (amount == 0 || price == 0) {
		return false;
	}

	// Tier validation — mirrors game.cpp:9411-9418
	const uint8_t maxTier = static_cast<uint8_t>(g_configManager().getNumber(FORGE_MAX_ITEM_TIER));
	if (tier > maxTier) {
		tier = maxTier;
	}
	if (tier > 0 && it.upgradeClassification == 0) {
		tier = 0;
	}

	const uint64_t totalPrice = price * static_cast<uint64_t>(amount);
	const uint64_t fee = IOMarket::feeFor(totalPrice);

	// Money theater only for AWAKE bots (present in the online map). Hibernated
	// bots skip it: their temp-player debit was discarded unpersisted anyway.
	const auto &bot = getPlayerByGUID(botGuid); // no offline load
	if (bot) {
		if (action == MARKETACTION_SELL) {
			// SELL: bot conjures items (skip removeOfferItems). Only fee is debited.
			if (fee > (bot->getMoney() + bot->getBankBalance())) {
				g_logger().warn("[botCreateMarketOffer] bot {} fee {} > funds for SELL", bot->getName(), fee);
				return false;
			}
			removeMoney(bot, fee, 0, true);
			g_metrics().addCounter("balance_decrease", fee, { { "player", bot->getName() }, { "context", "market_fee_bot" } });
		} else {
			// BUY: bot escrows totalPrice + fee (mirrors game.cpp:9462-9472)
			const uint64_t needed = totalPrice + fee;
			if (needed > (bot->getMoney() + bot->getBankBalance())) {
				g_logger().warn("[botCreateMarketOffer] bot {} needs {} for BUY but has {}+{} bank+pocket", bot->getName(), needed, bot->getBankBalance(), bot->getMoney());
				return false;
			}
			removeMoney(bot, needed, 0, true);
			g_metrics().addCounter("balance_decrease", needed, { { "player", bot->getName() }, { "context", "market_offer_bot" } });
		}
	}

	// Cap-guarded async INSERT on the DatabaseTasks worker. Mirrors
	// IOMarket::createOffer's column set; the WHERE clause enforces
	// maxMarketOffersAtATimePerPlayer atomically (cap 0 = unlimited, plain insert).
	const uint32_t maxOfferCount = g_configManager().getNumber(MAX_MARKET_OFFERS_AT_A_TIME_PER_PLAYER);
	std::string insertQuery;
	if (maxOfferCount == 0) {
		insertQuery = fmt::format(
			"INSERT INTO `market_offers` (`player_id`, `sale`, `itemtype`, `amount`, `created`, `anonymous`, `price`, `tier`) "
			"VALUES ({}, {}, {}, {}, {}, {}, {}, {})",
			botGuid, static_cast<int>(action), it.id, amount, time(nullptr), anonymous ? 1 : 0, price, static_cast<int>(tier)
		);
	} else {
		insertQuery = fmt::format(
			"INSERT INTO `market_offers` (`player_id`, `sale`, `itemtype`, `amount`, `created`, `anonymous`, `price`, `tier`) "
			"SELECT {}, {}, {}, {}, {}, {}, {}, {} FROM DUAL "
			"WHERE (SELECT `c` FROM (SELECT COUNT(*) AS `c` FROM `market_offers` WHERE `player_id` = {}) AS `t`) < {}",
			botGuid, static_cast<int>(action), it.id, amount, time(nullptr), anonymous ? 1 : 0, price, static_cast<int>(tier),
			botGuid, maxOfferCount
		);
	}
	g_botDatabaseTasks().execute(insertQuery);

	// PERF FIX (2026-05-27): skip bot save here. Bots have effectively unlimited
	// money and bot inventory is purely cosmetic — the market is just for "feels
	// alive" purposes (visible offers + counterparty trades). Persisting bot
	// money/inventory changes per market action was firing the 15-query sync save
	// chain on the dispatcher for every offer. Crash-time data loss accepted:
	// the async INSERT above DOES persist the offer row itself, which is the
	// only thing that needs to survive (so real players can see/accept it).
	// User explicit approval 2026-05-27.

	return true;
}

bool Game::botAcceptMarketOffer(uint32_t botGuid, uint32_t offerId, uint16_t amount) {
	if (getGameState() == GAME_STATE_SHUTDOWN || unresolvedMarketOffers_.contains(offerId)) return false;

	auto offer = IOMarket::getOfferById(offerId);
	if (!offer.id || amount == 0 || amount > offer.amount || offer.playerId == botGuid
		|| (offer.type != MARKETACTION_BUY && offer.type != MARKETACTION_SELL)) {
		return false;
	}
	const auto &itemType = Item::items[offer.itemId];
	if (!itemType.id || !itemType.wareId) return false;
	const uint8_t maxTier = static_cast<uint8_t>(g_configManager().getNumber(FORGE_MAX_ITEM_TIER));
	offer.tier = itemType.upgradeClassification > 0 ? std::min(offer.tier, maxTier) : 0;

	const auto bot = getPlayerByGUID(botGuid, true);
	const auto counterparty = getPlayerByGUID(offer.playerId, true);
	if (!bot || !counterparty || counterparty->isBotPlayer() || IOMarket::playerHasPendingFill(offer.playerId)) return false;

	const bool humanBuying = offer.type == MARKETACTION_BUY;
	if (!humanBuying && offer.price * amount > bot->getMoney() + bot->getBankBalance()) return false;
	const auto &recipient = humanBuying ? counterparty : bot;
	const auto inbox = recipient->getInbox();
	if (!inbox) return false;

	std::vector<std::shared_ptr<Item>> staged;
	uint32_t delivered = 0;
	uint64_t total = 0;
	uint64_t historyId = 0;
	DBTransaction::Outcome outcome;
	{
		Player::PlayerLock lock(counterparty);
		outcome = DBTransaction::executeWithOutcome([&] {
			if (!IOMarket::lockFillOffer(offer)) return false;
			recipient->addItemBatchToPaginedContainer(inbox, itemType.id, amount, delivered, FLAG_NOLIMIT, offer.tier, &staged);
			if (delivered == 0) return false;
			total = offer.price * delivered;
			const bool checkpoint = humanBuying ? IOLoginDataSave::savePlayerInbox(counterparty)
				: g_database().executeQuery(fmt::format("UPDATE players SET balance={} WHERE id={}",
					counterparty->getBankBalance() + total, offer.playerId));
			if (!checkpoint) return false;
			historyId = IOMarket::writeFill(offer, botGuid, static_cast<uint16_t>(delivered));
			return historyId != 0;
		});
		if (outcome == DBTransaction::Outcome::Committed && !humanBuying) {
			counterparty->setBankBalance(counterparty->getBankBalance() + total);
		}
		if (outcome != DBTransaction::Outcome::Committed) {
			for (const auto &item : staged) inbox->removeThingSilently(item, item->getItemCount());
		}
		if (outcome == DBTransaction::Outcome::Uncertain) {
			IOMarket::setPlayerFillPending(offer.playerId, true);
		}
	}

	auto publish = [this, counterparty, bot, recipient, inbox, staged, total, humanBuying](bool restoreInbox) {
		if (humanBuying) {
			bot->setBankBalance(bot->getBankBalance() + total);
		} else {
			if (restoreInbox) counterparty->setBankBalance(counterparty->getBankBalance() + total);
			const auto debit = std::min(total, bot->getBankBalance());
			bot->setBankBalance(bot->getBankBalance() - debit);
			removeMoney(bot, total - debit);
		}
		for (const auto &item : staged) {
			if (restoreInbox) inbox->internalAddThing(item);
			inbox->notifyStagedAddition(item);
		}
		if (recipient->isOnline()) recipient->onReceiveMail();
	};
	if (outcome == DBTransaction::Outcome::Uncertain) {
		unresolvedMarketOffers_.insert(offerId);
		g_logger().error("MARKET_COMMIT_UNCERTAIN offer_id={} history_id={}", offerId, historyId);
		if (counterparty->isOnline()) counterparty->removePlayer(true);
		reconcileMarketOffer(offerId, [counterparty, historyId, publish = std::move(publish)] {
			const auto committed = IOMarket::fillCommitted(historyId);
			if (!committed.has_value()) return false;
			if (*committed) publish(true);
			IOMarket::setPlayerFillPending(counterparty->getGUID(), false);
			g_saveManager().savePlayer(counterparty);
			return true;
		});
		return false;
	}
	if (outcome != DBTransaction::Outcome::Committed) return false;
	publish(false);
	return true;
}

void Game::reconcileMarketOffer(uint32_t offerId, std::function<bool()> resolve) {
	g_dispatcher().scheduleEvent(1000, [this, offerId, resolve = std::move(resolve)]() {
		if (resolve()) unresolvedMarketOffers_.erase(offerId);
		else reconcileMarketOffer(offerId, resolve);
	}, "Game::reconcileMarketOffer");
}

bool Game::payMarketGold(const std::shared_ptr<Player> &player, uint64_t gold, bool bankFirst) {
	if (!bankFirst) return removeMoney(player, gold, 0, true, true);
	const auto fromBank = std::min(gold, player->getBankBalance());
	if (!removeMoney(player, gold - fromBank, 0, false, true)) return false;
	player->setBankBalance(player->getBankBalance() - fromBank);
	return true;
}

bool Game::checkpointMarketPlayers(const std::vector<std::shared_ptr<Player>> &players) {
	// A failed settlement can then reload the last valid character, including unrelated progress.
	return std::ranges::all_of(players, [](const auto &player) {
		return !player->isOnline() || IOLoginData::savePlayer(player);
	});
}

void Game::reloadMarketPlayers(const std::vector<std::shared_ptr<Player>> &players, uint32_t offerId, std::function<std::optional<bool>()> receipt) {
	std::vector<uint32_t> identifiers;
	for (const auto &player : players) {
		const auto guid = player->getGUID();
		identifiers.push_back(guid);
		IOMarket::setPlayerFillPending(guid, true);
		if (player->isOnline()) {
			player->discardPersistence();
			player->removePlayer(true);
		}
	}

	if (!receipt) {
		for (const auto guid : identifiers) IOMarket::setPlayerFillPending(guid, false);
		return;
	}

	unresolvedMarketOffers_.insert(offerId);
	reconcileMarketOffer(offerId, [identifiers = std::move(identifiers), receipt = std::move(receipt)] {
		if (!receipt().has_value()) return false;
		for (const auto guid : identifiers) IOMarket::setPlayerFillPending(guid, false);
		return true;
	});
}

std::optional<uint32_t> Game::redeemStoreCoin(const std::shared_ptr<Player> &player, const std::shared_ptr<Item> &token) {
	if (!player || !token || token->getID() != ITEM_STORE_COIN) {
		return std::nullopt;
	}
	const auto guid = player->getGUID();
	const std::vector participants { player };
	DBTransaction::Outcome outcome;
	uint32_t amount = 0;
	bool fenced = false;
	bool removed = false;
	{
		const Player::PlayerLock lock(player);
		const auto account = player->getAccount();
		if (!account || !player->isOnline() || player->isBotPlayer() || player->isPersistenceDiscarded()
			|| IOMarket::playerHasPendingFill(guid) || g_saveManager().hasPendingLogout(guid)) {
			return std::nullopt;
		}

		// An open cylinder need not belong to the player or be included in their save.
		bool (*saveItems)(const std::shared_ptr<Player> &) = nullptr;
		for (auto item = token; item;) {
			const auto parent = item->getParent();
			if (!parent || parent->getThingIndex(item) < 0) break;
			if (parent.get() == player.get()) {
				saveItems = IOLoginDataSave::savePlayerItem;
				break;
			}
			if (parent.get() == player->getInbox().get()) {
				saveItems = IOLoginDataSave::savePlayerInbox;
				break;
			}
			if (player->getLastDepotId() != -1 && std::ranges::any_of(player->depotChests, [&](const auto &entry) {
					return parent.get() == entry.second.get();
				})) {
				saveItems = IOLoginDataSave::savePlayerDepotItems;
				break;
			}
			item = parent->getItem();
		}
		const auto count = token->getItemCount();
		if (!saveItems || count == 0 || !checkpointMarketPlayers(participants)) {
			return std::nullopt;
		}
		const auto marker = token->getCustomAttribute("storeCoinsCredited");
		amount = marker && (!marker->hasValue<bool>() || marker->getBool()) ? 0 : count;
		const auto accountId = account->getID();
		outcome = DBTransaction::executeWithOutcome([&] {
			auto &db = g_database();
			const auto wallet = db.storeQuery(fmt::format(
				"SELECT `coins_transferable` FROM `accounts` WHERE `id` = {} FOR UPDATE", accountId));
			const auto owner = db.storeQuery(fmt::format(
				"SELECT `id` FROM `players` WHERE `id` = {} AND `account_id` = {} AND `save` <> 0 FOR UPDATE", guid, accountId));
			if (!wallet || !owner) return false;
			const auto balance = wallet->getNumber<uint32_t>("coins_transferable");
			if (amount > std::numeric_limits<uint32_t>::max() - balance) return false;

			IOMarket::setPlayerFillPending(guid, true);
			fenced = true;
			removed = true;
			if (internalRemoveItem(token, count) != RETURNVALUE_NOERROR) {
				removed = false;
				return false;
			}
			if (token->getParent() || !saveItems(player)) return false;
			if (amount == 0) return true;
			auto &accounts = g_accountRepository();
			return accounts.setCoins(accountId, CoinType::Transferable, balance + amount)
				&& accounts.registerCoinsTransaction(accountId, CoinTransactionType::Add, amount, CoinType::Transferable, "Redeemed Store Coin item");
		});
		if (fenced && (!removed || outcome == DBTransaction::Outcome::Committed)) {
			IOMarket::setPlayerFillPending(guid, false);
		}
	}
	if (outcome == DBTransaction::Outcome::Committed && removed) {
		return amount;
	}
	if (outcome == DBTransaction::Outcome::Uncertain && removed) {
		reloadMarketPlayers(participants, 0, [guid]() -> std::optional<bool> {
			// Wait for the original writer's player-row lock before allowing a fresh load.
			const bool settled = DBTransaction::executeWithinTransaction([&] {
				bool read = false;
				g_database().storeQuery(fmt::format("SELECT `id` FROM `players` WHERE `id` = {} FOR UPDATE", guid), read);
				return read;
			});
			return settled ? std::optional { true } : std::nullopt;
		});
	} else if (removed) {
		reloadMarketPlayers(participants);
	}
	return std::nullopt;
}

bool Game::refundMarketOffer(const MarketOfferEx &offer, const std::shared_ptr<Player> &owner, MarketOfferState_t state, bool syntheticBot) {
	const bool buy = offer.type == MARKETACTION_BUY;
	if (!offer.id || !offer.amount || (owner && offer.playerId != owner->getGUID())
		|| (!owner && (!buy || syntheticBot || state != OFFERSTATE_EXPIRED))
		|| unresolvedMarketOffers_.contains(offer.id) || IOMarket::playerHasPendingFill(offer.playerId)
		|| g_saveManager().hasPendingLogout(offer.playerId)
		|| (!buy && offer.type != MARKETACTION_SELL)) {
		return false;
	}

	if (buy && offer.price > std::numeric_limits<uint64_t>::max() / offer.amount) return false;
	const uint64_t gold = buy ? offer.price * offer.amount : 0;
	const bool returnItems = !buy && !syntheticBot && offer.itemId != ITEM_STORE_COIN;
	const uint8_t tier = returnItems && Item::items[offer.itemId].upgradeClassification > 0 ? offer.tier : 0;
	const auto inbox = returnItems ? owner->getInbox() : nullptr;
	if (returnItems && !inbox) return false;

	std::vector<std::shared_ptr<Item>> staged;
	uint64_t historyId = 0;
	DBTransaction::Outcome outcome;
	{
		std::optional<Player::PlayerLock> lock;
		if (owner) lock.emplace(owner);
		if (owner && owner->getBankBalance() > std::numeric_limits<uint64_t>::max() - gold) return false;
		outcome = DBTransaction::executeWithOutcome([&] {
			if (!IOMarket::lockFillOffer(offer)) return false;
			if (buy && !syntheticBot) {
				uint64_t balance = owner ? owner->getBankBalance() : 0;
				if (!owner) {
					const auto row = g_database().storeQuery(fmt::format(
						"SELECT balance FROM players WHERE id={} FOR UPDATE", offer.playerId));
					if (!row) return false;
					balance = row->getNumber<uint64_t>("balance");
					if (balance > std::numeric_limits<uint64_t>::max() - gold) return false;
				}
				if (!g_database().executeQuery(fmt::format("UPDATE players SET balance={} WHERE id={}",
					balance + gold, offer.playerId))) return false;
			} else if (returnItems) {
				uint32_t delivered = 0;
				owner->addItemBatchToPaginedContainer(inbox, offer.itemId, offer.amount, delivered, FLAG_NOLIMIT, tier, &staged);
				if (delivered != offer.amount || !IOLoginDataSave::savePlayerInbox(owner)) return false;
			} else if (!buy && !syntheticBot) {
				const auto account = owner->getAccount();
				if (!account) return false;
				const auto balance = g_database().storeQuery(fmt::format(
					"SELECT coins_transferable FROM accounts WHERE id={} FOR UPDATE", account->getID()));
				if (!balance || balance->getNumber<uint32_t>("coins_transferable") > std::numeric_limits<uint32_t>::max() - offer.amount
					|| account->addCoins(CoinType::Transferable, offer.amount, "") != AccountErrors_t::Ok) return false;
			}
			historyId = IOMarket::writeClose(offer, state);
			return historyId != 0;
		});
		if (outcome == DBTransaction::Outcome::Committed) {
			if (owner && gold) owner->setBankBalance(owner->getBankBalance() + gold);
		} else {
			for (const auto &item : staged) inbox->removeThingSilently(item, item->getItemCount());
		}
		if (outcome == DBTransaction::Outcome::Uncertain && !syntheticBot) {
			IOMarket::setPlayerFillPending(offer.playerId, true);
		}
	}

	auto publish = [owner, inbox, staged = std::move(staged), gold, syntheticBot](bool restore) {
		if (!owner) return;
		if (restore) {
			Player::PlayerLock lock(owner);
			if (gold) owner->setBankBalance(owner->getBankBalance() + gold);
			for (const auto &item : staged) inbox->internalAddThing(item);
		}
		for (const auto &item : staged) inbox->notifyStagedAddition(item);
		if (gold) {
			g_metrics().addCounter("balance_increase", gold, { { "player", owner->getName() },
				{ "context", syntheticBot ? "market_purchase_refund_bot" : "market_purchase_refund" } });
		}
	};

	if (outcome == DBTransaction::Outcome::Uncertain) {
		unresolvedMarketOffers_.insert(offer.id);
		g_logger().error("MARKET_REFUND_COMMIT_UNCERTAIN offer_id={} history_id={}", offer.id, historyId);
		if (!syntheticBot && owner && owner->isOnline()) owner->removePlayer(true);
		reconcileMarketOffer(offer.id, [playerId = offer.playerId, syntheticBot, historyId, publish = std::move(publish)] {
			const auto committed = IOMarket::fillCommitted(historyId);
			if (!committed.has_value()) return false;
			if (*committed) publish(true);
			if (!syntheticBot) IOMarket::setPlayerFillPending(playerId, false);
			return true;
		});
		return false;
	}
	if (outcome != DBTransaction::Outcome::Committed) return false;
	publish(false);
	return true;
}

bool Game::botCancelMarketOffer(uint32_t botGuid, uint32_t offerId) {
	if (getGameState() == GAME_STATE_SHUTDOWN) return false;
	const auto offer = IOMarket::getOfferById(offerId);
	if (!offer.id || offer.playerId != botGuid) return false;
	return refundMarketOffer(offer, getPlayerByGUID(botGuid, true), OFFERSTATE_CANCELLED, true);
}
