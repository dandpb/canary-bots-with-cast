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
//     moveOfferToHistory for canonical DB writes.
//   - g_saveManager().savePlayer() for offline counterparties.
//
// IMPORTANT: when the user-facing market functions in game.cpp change, mirror those
// changes here. The two paths share no helper code; drift is the main risk.

#include "game/game.hpp"

#include "config/configmanager.hpp"
#include "creatures/players/player.hpp"
#include "database/botdatabasetasks.hpp" // bundle 6: dedicated bot-DB worker
#include "game/scheduling/save_manager.hpp"
#include "game/scheduling/dispatcher.hpp"
#include "io/functions/iologindata_save_player.hpp"
#include "io/iomarket.hpp"
#include "items/containers/inbox/inbox.hpp"
#include "items/items.hpp"
#include "lib/metrics/metrics.hpp"
#include "lua/scripts/lua_environment.hpp"

bool Game::botCreateMarketOffer(uint32_t botGuid, uint8_t action, uint16_t itemId, uint16_t amount, uint64_t price, uint8_t tier, bool anonymous) {
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
	if (unresolvedMarketOffers_.contains(offerId)) return false;

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
		reconcileBotMarketFill(offerId, [counterparty, historyId, publish = std::move(publish)] {
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

void Game::reconcileBotMarketFill(uint32_t offerId, std::function<bool()> resolve) {
	g_dispatcher().scheduleEvent(1000, [this, offerId, resolve = std::move(resolve)]() {
		if (resolve()) unresolvedMarketOffers_.erase(offerId);
		else reconcileBotMarketFill(offerId, resolve);
	}, "Game::reconcileBotMarketFill");
}

bool Game::botCancelMarketOffer(uint32_t botGuid, uint32_t offerId) {
	if (unresolvedMarketOffers_.contains(offerId)) return false;
	const auto &bot = getPlayerByGUID(botGuid, true);
	if (!bot) {
		return false;
	}

	MarketOfferEx offer = IOMarket::getOfferById(offerId);
	if (offer.id == 0 || offer.playerId != bot->getGUID()) {
		return false;
	}

	if (offer.type == MARKETACTION_BUY) {
		// Refund escrow to bot
		bot->setBankBalance(bot->getBankBalance() + offer.price * offer.amount);
		g_metrics().addCounter("balance_increase", offer.price * offer.amount, { { "player", bot->getName() }, { "context", "market_purchase_refund_bot" } });
	} else {
		// SELL cancel — items would normally go back to seller's inbox.
		// For bots, items were never debited from depot (botCreateMarketOffer skips that),
		// so we don't need to deliver anything back. The plan acknowledges this is intentional.
	}

	IOMarket::moveOfferToHistory(offer.id, OFFERSTATE_CANCELLED);

	// PERF FIX (2026-05-27): skip bot save (see botCreateMarketOffer above).
	// Refund of bot money is in-memory only — discarded with the temp Player
	// shared_ptr. Accepted per user.

	return true;
}
