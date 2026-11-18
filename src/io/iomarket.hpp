/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#pragma once

#include "database/database.hpp"
#include "declarations.hpp"
#include "lib/di/container.hpp"

class IOMarket {
public:
	IOMarket() = default;

	static IOMarket &getInstance() {
		return inject<IOMarket>();
	}

	static MarketOfferList getActiveOffers(MarketAction_t action);
	static MarketOfferList getActiveOffers(MarketAction_t action, uint16_t itemId, uint8_t tier);
	static MarketOfferList getOwnOffers(MarketAction_t action, uint32_t playerId);
	static HistoryMarketOfferList getOwnHistory(MarketAction_t action, uint32_t playerId);

	static void processExpiredOffers(const DBResult_ptr &result, bool);
	static void checkExpiredOffers();

	static uint32_t getPlayerOfferCount(uint32_t playerId);
	static MarketOfferEx getOfferByCounter(uint32_t timestamp, uint16_t counter);
	static MarketOfferEx getOfferById(uint32_t offerId);

	static void createOffer(uint32_t playerId, MarketAction_t action, uint32_t itemId, uint16_t amount, uint64_t price, uint8_t tier, bool anonymous);
	static constexpr uint64_t feeFor(uint64_t total) {
		return std::clamp<uint64_t>(total / 50, 20, 1'000'000);
	}
	static bool lockFillOffer(const MarketOfferEx &offer);
	static uint64_t writeFill(const MarketOfferEx &offer, uint32_t takerId, uint16_t amount);
	static std::optional<bool> fillCommitted(uint64_t historyId);
	static bool playerHasPendingFill(uint32_t guid);
	static void setPlayerFillPending(uint32_t guid, bool pending);
	static void acceptOffer(uint32_t offerId, uint16_t amount);
	static void deleteOffer(uint32_t offerId);

	static void appendHistory(uint32_t playerId, MarketAction_t type, uint16_t itemId, uint16_t amount, uint64_t price, time_t timestamp, uint8_t tier, MarketOfferState_t state);
	static bool moveOfferToHistory(uint32_t offerId, MarketOfferState_t state);

	void updateStatistics();

	using StatisticsMap = std::map<uint16_t, std::map<uint8_t, MarketStatistics>>;
	StatisticsMap getPurchaseStatistics() const;
	StatisticsMap getSaleStatistics() const;
	struct StatisticsSnapshot {
		std::optional<MarketStatistics> purchase;
		std::optional<MarketStatistics> sale;
	};
	StatisticsSnapshot getStatistics(uint16_t itemId, uint8_t tier) const;

	static uint8_t getTierFromDatabaseTable(const std::string &string);

private:
	// [uint16_t = item id, [uint8_t = item tier, MarketStatistics = structure of the statistics]]
	StatisticsMap purchaseStatistics;
	StatisticsMap saleStatistics;
	mutable std::mutex statisticsMutex;
};
