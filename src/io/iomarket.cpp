/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "io/iomarket.hpp"

#include "config/configmanager.hpp"
#include "database/databasetasks.hpp"
#include "game/game.hpp"
#include "game/scheduling/dispatcher.hpp"
#include "creatures/players/player.hpp"

uint8_t IOMarket::getTierFromDatabaseTable(const std::string &string) {
	auto tier = static_cast<uint8_t>(std::atoi(string.c_str()));
	if (tier > g_configManager().getNumber(FORGE_MAX_ITEM_TIER)) {
		g_logger().error("{} - Failed to get number value {} for tier table result", __FUNCTION__, tier);
		return 0;
	}

	return tier;
}

MarketOfferList IOMarket::getActiveOffers(MarketAction_t action) {
	MarketOfferList offerList;

	std::string query = fmt::format(
		"SELECT `id`, `itemtype`, `amount`, `price`, `tier`, `created`, `anonymous`, "
		"(SELECT `name` FROM `players` WHERE `id` = `player_id`) AS `player_name` "
		"FROM `market_offers` WHERE `sale` = {}",
		action
	);

	DBResult_ptr result = g_database().storeQuery(query);
	if (!result) {
		return offerList;
	}

	const int32_t marketOfferDuration = g_configManager().getNumber(MARKET_OFFER_DURATION);

	do {
		MarketOffer offer;
		offer.itemId = result->getNumber<uint16_t>("itemtype");
		offer.amount = result->getNumber<uint16_t>("amount");
		offer.price = result->getNumber<uint64_t>("price");
		offer.timestamp = result->getNumber<uint32_t>("created") + marketOfferDuration;
		offer.counter = (result->getNumber<uint32_t>("id") ^ 0xABCDEF) & 0xFFFF;
		if (result->getNumber<uint16_t>("anonymous") == 0) {
			offer.playerName = result->getString("player_name");
		} else {
			offer.playerName = "Anonymous";
		}
		offer.tier = getTierFromDatabaseTable(result->getString("tier"));
		offerList.push_back(offer);
	} while (result->next());
	return offerList;
}

MarketOfferList IOMarket::getActiveOffers(MarketAction_t action, uint16_t itemId, uint8_t tier) {
	MarketOfferList offerList;

	const std::string priceOrder = (action == MARKETACTION_BUY) ? "DESC" : "ASC";
	std::ostringstream query;
	query << "SELECT `id`, `amount`, `price`, `tier`, `created`, `anonymous`, (SELECT `name` FROM `players` WHERE `id` = `player_id`) AS `player_name` FROM `market_offers` WHERE `sale` = " << action << " AND `itemtype` = " << itemId << " AND `tier` = " << std::to_string(tier) << " ORDER BY `price` " << priceOrder << ", `created` ASC";

	DBResult_ptr result = Database::getInstance().storeQuery(query.str());
	if (!result) {
		return offerList;
	}

	const int32_t marketOfferDuration = g_configManager().getNumber(MARKET_OFFER_DURATION);

	do {
		MarketOffer offer;
		offer.itemId = itemId;
		offer.amount = result->getNumber<uint16_t>("amount");
		offer.price = result->getNumber<uint64_t>("price");
		offer.timestamp = result->getNumber<uint32_t>("created") + marketOfferDuration;
		offer.counter = (result->getNumber<uint32_t>("id") ^ 0xABCDEF) & 0xFFFF;
		if (result->getNumber<uint16_t>("anonymous") == 0) {
			offer.playerName = result->getString("player_name");
		} else {
			offer.playerName = "Anonymous";
		}
		offer.tier = getTierFromDatabaseTable(result->getString("tier"));
		offerList.push_back(offer);
	} while (result->next());
	return offerList;
}

MarketOfferList IOMarket::getOwnOffers(MarketAction_t action, uint32_t playerId) {
	MarketOfferList offerList;

	const int32_t marketOfferDuration = g_configManager().getNumber(MARKET_OFFER_DURATION);

	std::ostringstream query;
	query << "SELECT `id`, `amount`, `price`, `created`, `itemtype`, `tier` FROM `market_offers` WHERE `player_id` = " << playerId << " AND `sale` = " << action << " ORDER BY `created` ASC";

	DBResult_ptr result = Database::getInstance().storeQuery(query.str());
	if (!result) {
		return offerList;
	}

	do {
		MarketOffer offer;
		offer.amount = result->getNumber<uint16_t>("amount");
		offer.price = result->getNumber<uint64_t>("price");
		offer.timestamp = result->getNumber<uint32_t>("created") + marketOfferDuration;
		offer.counter = (result->getNumber<uint32_t>("id") ^ 0xABCDEF) & 0xFFFF;
		offer.itemId = result->getNumber<uint16_t>("itemtype");
		offer.tier = getTierFromDatabaseTable(result->getString("tier"));
		offerList.push_back(offer);
	} while (result->next());
	return offerList;
}

HistoryMarketOfferList IOMarket::getOwnHistory(MarketAction_t action, uint32_t playerId) {
	HistoryMarketOfferList offerList;

	std::ostringstream query;
	query << "SELECT `itemtype`, `amount`, `price`, `expires_at`, `state`, `tier` FROM `market_history` WHERE `player_id` = " << playerId << " AND `sale` = " << action;

	DBResult_ptr result = Database::getInstance().storeQuery(query.str());
	if (!result) {
		return offerList;
	}

	do {
		HistoryMarketOffer offer {};
		offer.itemId = result->getNumber<uint16_t>("itemtype");
		offer.amount = result->getNumber<uint16_t>("amount");
		offer.price = result->getNumber<uint64_t>("price");
		offer.timestamp = result->getNumber<uint32_t>("expires_at");
		offer.tier = getTierFromDatabaseTable(result->getString("tier"));

		MarketOfferState_t offerState = static_cast<MarketOfferState_t>(result->getNumber<uint16_t>("state"));
		if (offerState == OFFERSTATE_ACCEPTEDEX) {
			offerState = OFFERSTATE_ACCEPTED;
		}

		offer.state = offerState;

		offerList.push_back(offer);
	} while (result->next());
	return offerList;
}

void IOMarket::processExpiredOffers(const DBResult_ptr &result, bool) {
	if (!result || g_game().getGameState() == GAME_STATE_SHUTDOWN) {
		return;
	}

	const auto expiryCutoff = getTimeNow() - g_configManager().getNumber(MARKET_OFFER_DURATION);
	do {
		const auto offer = getOfferById(result->getNumber<uint32_t>("id"));
		if (!offer.id || offer.timestamp > expiryCutoff) continue;

		const auto owner = g_game().getPlayerByGUID(offer.playerId, offer.type == MARKETACTION_SELL);
		g_game().refundMarketOffer(offer, owner, OFFERSTATE_EXPIRED);
	} while (result->next());
}

void IOMarket::checkExpiredOffers() {
	const time_t lastExpireDate = getTimeNow() - g_configManager().getNumber(MARKET_OFFER_DURATION);

	std::ostringstream query;
	query << "SELECT `id` FROM `market_offers` WHERE `created` <= " << lastExpireDate;
	g_databaseTasks().store(query.str(), IOMarket::processExpiredOffers);

	int32_t checkExpiredMarketOffersEachMinutes = g_configManager().getNumber(CHECK_EXPIRED_MARKET_OFFERS_EACH_MINUTES);
	if (checkExpiredMarketOffersEachMinutes <= 0) {
		return;
	}

	g_dispatcher().scheduleEvent(checkExpiredMarketOffersEachMinutes * 60 * 1000, IOMarket::checkExpiredOffers, __FUNCTION__, DispatcherLane::Maintenance);
}

std::optional<uint32_t> IOMarket::getPlayerOfferCount(uint32_t playerId) {
	std::ostringstream query;
	query << "SELECT COUNT(*) AS `count` FROM `market_offers` WHERE `player_id` = " << playerId;

	DBResult_ptr result = Database::getInstance().storeQuery(query.str());
	if (!result) {
		return std::nullopt;
	}
	return result->getNumber<uint32_t>("count");
}

MarketOfferEx IOMarket::getOfferByCounter(uint32_t timestamp, uint16_t counter) {
	MarketOfferEx offer;

	const int32_t created = timestamp - g_configManager().getNumber(MARKET_OFFER_DURATION);

	std::ostringstream query;
	query << "SELECT `id`, `sale`, `itemtype`, `amount`, `created`, `price`, `player_id`, `anonymous`, `tier`, (SELECT `name` FROM `players` WHERE `id` = `player_id`) AS `player_name` FROM `market_offers` WHERE `created` = " << created << " AND ((`id` ^ 0xABCDEF) & 65535) = " << counter << " LIMIT 1";

	DBResult_ptr result = Database::getInstance().storeQuery(query.str());
	if (!result) {
		offer.id = 0;
		return offer;
	}

	offer.id = result->getNumber<uint32_t>("id");
	offer.type = static_cast<MarketAction_t>(result->getNumber<uint16_t>("sale"));
	offer.amount = result->getNumber<uint16_t>("amount");
	offer.counter = (result->getNumber<uint32_t>("id") ^ 0xABCDEF) & 0xFFFF;
	offer.timestamp = result->getNumber<uint32_t>("created");
	offer.price = result->getNumber<uint64_t>("price");
	offer.itemId = result->getNumber<uint16_t>("itemtype");
	offer.playerId = result->getNumber<uint32_t>("player_id");
	offer.tier = getTierFromDatabaseTable(result->getString("tier"));
	if (result->getNumber<uint16_t>("anonymous") == 0) {
		offer.playerName = result->getString("player_name");
	} else {
		offer.playerName = "Anonymous";
	}
	return offer;
}

MarketOfferEx IOMarket::getOfferById(uint32_t offerId) {
	MarketOfferEx offer;
	offer.id = 0;

	std::ostringstream query;
	query << "SELECT `id`, `sale`, `itemtype`, `amount`, `created`, `price`, `player_id`, `anonymous`, `tier`, (SELECT `name` FROM `players` WHERE `id` = `player_id`) AS `player_name` FROM `market_offers` WHERE `id` = " << offerId << " LIMIT 1";

	DBResult_ptr result = Database::getInstance().storeQuery(query.str());
	if (!result) {
		return offer;
	}

	offer.id = result->getNumber<uint32_t>("id");
	offer.type = static_cast<MarketAction_t>(result->getNumber<uint16_t>("sale"));
	offer.amount = result->getNumber<uint16_t>("amount");
	offer.counter = (offer.id ^ 0xABCDEF) & 0xFFFF;
	offer.timestamp = result->getNumber<uint32_t>("created");
	offer.price = result->getNumber<uint64_t>("price");
	offer.itemId = result->getNumber<uint16_t>("itemtype");
	offer.playerId = result->getNumber<uint32_t>("player_id");
	offer.tier = getTierFromDatabaseTable(result->getString("tier"));
	if (result->getNumber<uint16_t>("anonymous") == 0) {
		offer.playerName = result->getString("player_name");
	} else {
		offer.playerName = "Anonymous";
	}
	return offer;
}

uint32_t IOMarket::createOffer(uint32_t playerId, MarketAction_t action, uint32_t itemId, uint16_t amount, uint64_t price, uint8_t tier, bool anonymous) {
	std::ostringstream query;
	query << "INSERT INTO `market_offers` (`player_id`, `sale`, `itemtype`, `amount`, `created`, `anonymous`, `price`, `tier`) VALUES (" << playerId << ',' << action << ',' << itemId << ',' << amount << ',' << getTimeNow() << ',' << anonymous << ',' << price << ',' << std::to_string(tier) << ')';
	auto &database = g_database();
	return database.executeQuery(query.str()) ? static_cast<uint32_t>(database.getLastInsertId()) : 0;
}

bool IOMarket::lockFillOffer(const MarketOfferEx &offer) {
	const auto row = g_database().storeQuery(fmt::format(
		"SELECT amount FROM market_offers WHERE id={} AND player_id={} AND price={} AND sale={} AND itemtype={} FOR UPDATE",
		offer.id, offer.playerId, offer.price, static_cast<unsigned>(offer.type), offer.itemId));
	return row && row->getNumber<uint16_t>("amount") == offer.amount;
}

uint64_t IOMarket::writeFill(const MarketOfferEx &offer, uint32_t takerId, uint16_t amount) {
	if (amount == 0 || amount > offer.amount) return 0;
	auto &database = g_database();
	const bool updated = amount == offer.amount
		? database.executeQuery(fmt::format("DELETE FROM market_offers WHERE id={}", offer.id))
		: database.executeQuery(fmt::format("UPDATE market_offers SET amount={} WHERE id={}", offer.amount - amount, offer.id));
	if (!updated) return 0;

	const auto now = getTimeNow();
	const auto opposite = offer.type == MARKETACTION_BUY ? MARKETACTION_SELL : MARKETACTION_BUY;
	const bool written = database.executeQuery(fmt::format(
		"INSERT INTO market_history (player_id, sale, itemtype, amount, price, expires_at, inserted, state, tier)"
		" VALUES ({},{},{},{},{},{},{},{},{}), ({},{},{},{},{},{},{},{},{})",
		takerId, static_cast<unsigned>(opposite), offer.itemId, amount, offer.price, now, now,
		static_cast<unsigned>(OFFERSTATE_ACCEPTEDEX), offer.tier,
		offer.playerId, static_cast<unsigned>(offer.type), offer.itemId, amount, offer.price, now, now,
		static_cast<unsigned>(OFFERSTATE_ACCEPTED), offer.tier));
	return written ? database.getLastInsertId() : 0;
}

namespace {
std::optional<bool> marketReceiptExists(std::string_view table, uint64_t id) {
	bool found = false;
	if (!DBTransaction::executeWithinTransaction([&] {
			bool readSucceeded = false;
			const auto row = g_database().storeQuery(fmt::format(
				"SELECT id FROM {} WHERE id={} FOR UPDATE", table, id), readSucceeded);
			found = row != nullptr;
			return readSucceeded;
		})) return std::nullopt;
	return found;
}
}

std::optional<bool> IOMarket::fillCommitted(uint64_t historyId) {
	return marketReceiptExists("market_history", historyId);
}

std::optional<bool> IOMarket::offerCreated(uint32_t offerId) {
	return marketReceiptExists("market_offers", offerId);
}

namespace {
std::mutex pendingMarketPlayersMutex;
std::unordered_set<uint32_t> pendingMarketPlayers;
}

bool IOMarket::playerHasPendingFill(uint32_t guid) {
	std::lock_guard lock(pendingMarketPlayersMutex);
	return pendingMarketPlayers.contains(guid);
}

void IOMarket::setPlayerFillPending(uint32_t guid, bool pending) {
	std::lock_guard lock(pendingMarketPlayersMutex);
	if (pending) pendingMarketPlayers.insert(guid);
	else pendingMarketPlayers.erase(guid);
}

void IOMarket::acceptOffer(uint32_t offerId, uint16_t amount) {
	std::ostringstream query;
	query << "UPDATE `market_offers` SET `amount` = `amount` - " << amount << " WHERE `id` = " << offerId;
	Database::getInstance().executeQuery(query.str());
}

void IOMarket::deleteOffer(uint32_t offerId) {
	std::ostringstream query;
	query << "DELETE FROM `market_offers` WHERE `id` = " << offerId;
	Database::getInstance().executeQuery(query.str());
}

void IOMarket::appendHistory(uint32_t playerId, MarketAction_t type, uint16_t itemId, uint16_t amount, uint64_t price, time_t timestamp, uint8_t tier, MarketOfferState_t state) {
	std::ostringstream query;
	query << "INSERT INTO `market_history` (`player_id`, `sale`, `itemtype`, `amount`, `price`, `expires_at`, `inserted`, `state`, `tier`) VALUES ("
		  << playerId << ',' << type << ',' << itemId << ',' << amount << ',' << price << ','
		  << timestamp << ',' << getTimeNow() << ',' << state << ',' << std::to_string(tier) << ')';
	g_databaseTasks().execute(query.str());
}

uint64_t IOMarket::writeClose(const MarketOfferEx &offer, MarketOfferState_t state) {
	auto &database = g_database();
	if (!database.executeQuery(fmt::format("DELETE FROM market_offers WHERE id={}", offer.id))) return 0;

	const auto now = getTimeNow();
	const bool written = database.executeQuery(fmt::format(
		"INSERT INTO market_history (player_id, sale, itemtype, amount, price, expires_at, inserted, state, tier)"
		" VALUES ({},{},{},{},{},{},{},{},{})",
		offer.playerId, static_cast<unsigned>(offer.type), offer.itemId, offer.amount, offer.price, now, now,
		static_cast<unsigned>(state), offer.tier));
	return written ? database.getLastInsertId() : 0;
}

void IOMarket::updateStatistics() {
	auto query = fmt::format(
		"SELECT sale, itemtype, COUNT(price) AS num, MIN(price) AS min, MAX(price) AS max, SUM(price) AS sum, tier "
		"FROM market_history "
		"WHERE state = '{}' "
		"GROUP BY itemtype, sale, tier",
		OFFERSTATE_ACCEPTED
	);

	DBResult_ptr result = g_database().storeQuery(query);
	if (!result) {
		return;
	}

	StatisticsMap newPurchase;
	StatisticsMap newSale;

	do {
		const auto tier = getTierFromDatabaseTable(result->getString("tier"));
		const auto itemId = result->getNumber<uint16_t>("itemtype");
		auto &statistics = (result->getNumber<uint16_t>("sale") == MARKETACTION_BUY)
			? newPurchase[itemId][tier]
			: newSale[itemId][tier];

		statistics.numTransactions = result->getNumber<uint32_t>("num");
		statistics.lowestPrice = result->getNumber<uint64_t>("min");
		statistics.totalPrice = result->getNumber<uint64_t>("sum");
		statistics.highestPrice = result->getNumber<uint64_t>("max");
	} while (result->next());

	{
		std::scoped_lock lock(statisticsMutex);
		purchaseStatistics.swap(newPurchase);
		saleStatistics.swap(newSale);
	}
}

IOMarket::StatisticsMap IOMarket::getPurchaseStatistics() const {
	std::scoped_lock lock(statisticsMutex);
	return purchaseStatistics;
}

IOMarket::StatisticsMap IOMarket::getSaleStatistics() const {
	std::scoped_lock lock(statisticsMutex);
	return saleStatistics;
}

IOMarket::StatisticsSnapshot IOMarket::getStatistics(uint16_t itemId, uint8_t tier) const {
	StatisticsSnapshot snapshot;
	std::scoped_lock lock(statisticsMutex);

	if (const auto purchaseIt = purchaseStatistics.find(itemId); purchaseIt != purchaseStatistics.end()) {
		if (const auto tierIt = purchaseIt->second.find(tier); tierIt != purchaseIt->second.end()) {
			snapshot.purchase = tierIt->second;
		}
	}

	if (const auto saleIt = saleStatistics.find(itemId); saleIt != saleStatistics.end()) {
		if (const auto tierIt = saleIt->second.find(tier); tierIt != saleIt->second.end()) {
			snapshot.sale = tierIt->second;
		}
	}

	return snapshot;
}
