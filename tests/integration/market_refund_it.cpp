#include "creatures/players/player.hpp"
#include "database/database.hpp"
#include "game/game.hpp"
#include "io/iomarket.hpp"

#include <gtest/gtest.h>

namespace {
class MarketRefund : public testing::Test {
protected:
	Database &database = g_database();
	MarketOfferEx offer;

	void SetUp() override {
		ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE players (id INT PRIMARY KEY, balance BIGINT UNSIGNED) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery(
			"CREATE TEMPORARY TABLE market_offers (id INT PRIMARY KEY, player_id INT, amount INT, "
			"price BIGINT UNSIGNED, sale INT, itemtype INT) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery(
			"CREATE TEMPORARY TABLE market_history (id INT AUTO_INCREMENT PRIMARY KEY, player_id INT UNIQUE, "
			"sale INT, itemtype INT, amount INT, price BIGINT UNSIGNED, expires_at BIGINT, inserted BIGINT, state INT, tier INT) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery("INSERT INTO players VALUES (7,100)"));
		ASSERT_TRUE(database.executeQuery("INSERT INTO market_offers VALUES (1,7,4,3,0,9)"));
		offer.id = 1;
		offer.playerId = 7;
		offer.amount = 4;
		offer.price = 3;
		offer.type = MARKETACTION_BUY;
		offer.itemId = 9;
	}

	void TearDown() override {
		EXPECT_TRUE(database.executeQuery("DROP TEMPORARY TABLE IF EXISTS market_history, market_offers, players"));
	}

	void expectUnchangedOffer() {
		const auto balance = database.storeQuery("SELECT balance FROM players WHERE id=7");
		const auto active = database.storeQuery("SELECT amount FROM market_offers WHERE id=1");
		ASSERT_TRUE(balance && active);
		EXPECT_EQ(balance->getNumber<uint64_t>("balance"), 100);
		EXPECT_EQ(active->getNumber<uint16_t>("amount"), 4);
	}
};
}

TEST_F(MarketRefund, ExpiryRejectsAStaleAmountAndRefundsOnlyWhatRemains) {
	offer.amount = 10;
	EXPECT_FALSE(g_game().refundMarketOffer(offer, nullptr, OFFERSTATE_EXPIRED));
	expectUnchangedOffer();

	offer.amount = 4;
	ASSERT_TRUE(g_game().refundMarketOffer(offer, nullptr, OFFERSTATE_EXPIRED));
	EXPECT_FALSE(database.storeQuery("SELECT id FROM market_offers WHERE id=1"));
	const auto balance = database.storeQuery("SELECT balance FROM players WHERE id=7");
	const auto history = database.storeQuery("SELECT id, amount, state FROM market_history WHERE player_id=7");
	ASSERT_TRUE(balance && history);
	EXPECT_EQ(balance->getNumber<uint64_t>("balance"), 112);
	EXPECT_EQ(history->getNumber<uint16_t>("amount"), 4);
	EXPECT_EQ(history->getNumber<MarketOfferState_t>("state"), OFFERSTATE_EXPIRED);
	EXPECT_EQ(IOMarket::fillCommitted(history->getNumber<uint64_t>("id")), true);
}

TEST_F(MarketRefund, FailedHistoryWriteLeavesTheOfferAndRefundUntouched) {
	ASSERT_TRUE(database.executeQuery("INSERT INTO market_history (player_id) VALUES (7)"));
	const auto owner = std::make_shared<Player>();
	owner->setGUID(7);
	owner->setBankBalance(100);

	EXPECT_FALSE(g_game().refundMarketOffer(offer, owner, OFFERSTATE_CANCELLED));
	expectUnchangedOffer();
	EXPECT_EQ(owner->getBankBalance(), 100);
}
