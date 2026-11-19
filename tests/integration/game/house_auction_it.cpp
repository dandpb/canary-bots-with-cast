#include "database/database.hpp"
#include "io/iomapserialize.hpp"

#include <gtest/gtest.h>

namespace {
class HouseAuctionSettlement : public testing::Test {
protected:
	static constexpr uint16_t furnishingId = ITEM_INBOX + 1;
	Database &database = g_database();
	Houses houses;
	std::shared_ptr<House> house;
	size_t originalItemCount = 0;

	void SetUp() override {
		auto &items = Item::items.getItems();
		originalItemCount = items.size();
		if (items.size() <= furnishingId) items.resize(furnishingId + 1);
		house = houses.addHouse(1);
		ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE players (id INT PRIMARY KEY, name VARCHAR(255), account_id INT, balance BIGINT UNSIGNED CHECK (balance <= 500)) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE server_config (config VARCHAR(50) PRIMARY KEY, value VARCHAR(256) NOT NULL) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery(
			"CREATE TEMPORARY TABLE houses (id INT PRIMARY KEY, owner INT, new_owner INT DEFAULT -1, name VARCHAR(255), town_id INT, rent INT, "
			"size INT, beds INT, paid INT, warnings INT, bidder INT, bidder_name VARCHAR(255), highest_bid INT, internal_bid INT, bid_end_date INT, "
			"state SMALLINT, transfer_status BOOL) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery("INSERT INTO players VALUES (1, 'Previous Bidder', 100, 210), (2, 'New Bidder', 101, 300)"));
		ASSERT_TRUE(database.executeQuery(
			"INSERT INTO houses (id, owner, rent, bidder, bidder_name, highest_bid, internal_bid, bid_end_date, state, transfer_status) "
			"VALUES (1, 0, 10, 1, 'Previous Bidder', 40, 100, 100000, 0, false)"));
		house->setAuctionState({1, "Previous Bidder", 40, 100, 100000, CyclopediaHouseState::Available, false, 10});
	}

	void TearDown() override {
		EXPECT_TRUE(database.executeQuery("DROP TEMPORARY TABLE IF EXISTS tile_store, house_lists, player_inboxitems, houses, server_config, players"));
		house.reset();
		Item::items.getItems().resize(originalItemCount);
	}

	void prepareFurnitureTransfer() {
		house->setTownId(1);
		ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE tile_store (house_id INT, data BLOB) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE house_lists (house_id INT) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE player_inboxitems (player_id INT, sid INT, pid INT, itemtype INT, count INT, attributes BLOB, PRIMARY KEY(player_id, sid)) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery("INSERT INTO tile_store VALUES (1, X'01'), (2, X'02')"));
		ASSERT_TRUE(database.executeQuery("INSERT INTO house_lists VALUES (1), (2)"));
		ASSERT_TRUE(database.executeQuery("INSERT INTO player_inboxitems VALUES (1, 205, 0, 101, 1, X'08')"));
		ASSERT_TRUE(database.executeQuery("UPDATE houses SET `owner`=1, new_owner=0, bidder=0, bidder_name='', highest_bid=0, internal_bid=0, bid_end_date=0, state=2 WHERE id=1"));
		house->setAuctionState({0, {}, 0, 0, 0, CyclopediaHouseState::Rented});
		ASSERT_TRUE(IOMapSerialize::settleHouseAuction(house, {}, {}, {}, IOMapSerialize::StartupHouseOwnership {0, 1, 0}));
		const auto pending = database.storeQuery("SELECT value FROM server_config WHERE config='house:depot:1'");
		ASSERT_TRUE(pending);
		EXPECT_EQ(pending->getString("value"), "1");

		auto &furnishing = Item::items.getItemType(furnishingId);
		furnishing.id = furnishingId;
		furnishing.pickupable = true;
		furnishing.movable = true;
		const auto tile = std::make_shared<HouseTile>(Position {100, 100, 7}, house);
		house->addTile(tile);
		const auto item = Item::CreateItem(furnishingId);
		ASSERT_TRUE(item);
		tile->internalAddThing(0, item);
	}

	void expectBalance(uint32_t guid, uint64_t expected) {
		const auto row = database.storeQuery(fmt::format("SELECT balance FROM players WHERE id={}", guid));
		ASSERT_TRUE(row);
		EXPECT_EQ(row->getNumber<uint64_t>("balance"), expected);
	}

	void expectEscrow(uint32_t guid, uint64_t bid) {
		const auto row = database.storeQuery("SELECT bidder, internal_bid FROM houses WHERE id=1");
		ASSERT_TRUE(row);
		EXPECT_EQ(row->getNumber<uint32_t>("bidder"), guid);
		EXPECT_EQ(row->getNumber<uint64_t>("internal_bid"), bid);
		EXPECT_EQ(house->getBidder(), guid);
		EXPECT_EQ(house->getInternalBid(), bid);
	}
};
}

TEST_F(HouseAuctionSettlement, OutbidPublishesBothBalancesAndTheNewEscrow) {
	const HouseAuctionState replacement {2, "New Bidder", 101, 125, 100000, CyclopediaHouseState::Available, false, 10};
	ASSERT_TRUE(IOMapSerialize::settleHouseAuction(house, replacement, {2, 135, true}, {1, 110}));
	expectBalance(1, 320);
	expectBalance(2, 165);
	expectEscrow(2, 125);
}

TEST_F(HouseAuctionSettlement, RejectedRefundPreservesTheHeldEscrowAndRollsBackTheDebit) {
	ASSERT_TRUE(database.executeQuery("UPDATE players SET balance=495 WHERE id=2"));
	ASSERT_TRUE(database.executeQuery("UPDATE houses SET bidder=2, bidder_name='Previous Bidder' WHERE id=1"));
	house->setBidder(2);
	const HouseAuctionState replacement {1, "New Bidder", 101, 130, 100000, CyclopediaHouseState::Available, false, 10};
	EXPECT_FALSE(IOMapSerialize::settleHouseAuction(house, replacement, {1, 140, true}, {2, 110}));
	expectBalance(1, 210);
	expectBalance(2, 495);
	expectEscrow(2, 100);
	EXPECT_FALSE(database.storeQuery("SELECT value FROM server_config"));
}

TEST_F(HouseAuctionSettlement, StaleEscrowCannotBeRefundedOrReplaced) {
	ASSERT_TRUE(database.executeQuery("UPDATE houses SET bidder=2, internal_bid=125 WHERE id=1"));
	HouseAuctionState cleared;
	cleared.state = CyclopediaHouseState::Rented;
	EXPECT_FALSE(IOMapSerialize::settleHouseAuction(house, cleared, {1, 110}, {}));
	expectBalance(1, 210);
	const auto persisted = database.storeQuery("SELECT bidder, internal_bid FROM houses WHERE id=1");
	ASSERT_TRUE(persisted);
	EXPECT_EQ(persisted->getNumber<uint32_t>("bidder"), 2);
	EXPECT_EQ(persisted->getNumber<uint64_t>("internal_bid"), 125);
	EXPECT_EQ(house->getBidder(), 1);
}

TEST_F(HouseAuctionSettlement, ProxyBidKeepsTheRentOriginallyHeldAfterRentChanges) {
	house->setRent(25);
	auto auction = house->getAuctionState();
	auction.highestBid = 60;
	ASSERT_TRUE(IOMapSerialize::settleHouseAuction(house, auction, {}, {}));
	const auto persisted = database.storeQuery("SELECT rent, highest_bid FROM houses WHERE id=1");
	ASSERT_TRUE(persisted);
	EXPECT_EQ(persisted->getNumber<uint32_t>("rent"), 10);
	EXPECT_EQ(persisted->getNumber<uint64_t>("highest_bid"), 60);
	EXPECT_EQ(house->getAuctionState().reservedRent, 10);
	expectBalance(1, 210);
}

TEST_F(HouseAuctionSettlement, StartupPublishesWinnerOwnershipAndClearsTheFundedEscrow) {
	HouseAuctionState cleared;
	cleared.state = CyclopediaHouseState::Rented;
	ASSERT_TRUE(IOMapSerialize::settleHouseAuction(house, cleared, {1, 60}, {}, IOMapSerialize::StartupHouseOwnership {1}));
	expectBalance(1, 270);
	expectEscrow(0, 0);
	const auto settled = database.storeQuery("SELECT owner, state FROM houses WHERE id=1");
	ASSERT_TRUE(settled);
	EXPECT_EQ(settled->getNumber<uint32_t>("owner"), 1);
	EXPECT_EQ(settled->getNumber<CyclopediaHouseState>("state"), CyclopediaHouseState::Rented);
	EXPECT_EQ(house->getOwner(), 1);
	EXPECT_EQ(house->getState(), CyclopediaHouseState::Rented);
}

TEST_F(HouseAuctionSettlement, StartupFurnitureAppendsInboxAndClearsOnlyItsOwnTilesAndObligation) {
	ASSERT_NO_FATAL_FAILURE(prepareFurnitureTransfer());
	ASSERT_NO_THROW(IOMapSerialize::completeStartupHouseDepotTransfers(houses));
	ASSERT_NO_THROW(IOMapSerialize::completeStartupHouseDepotTransfers(houses));
	const auto inbox = database.storeQuery("SELECT sid, itemtype FROM player_inboxitems WHERE player_id=1 ORDER BY sid");
	ASSERT_TRUE(inbox);
	EXPECT_EQ(inbox->getNumber<uint32_t>("sid"), 205);
	EXPECT_EQ(inbox->getNumber<uint32_t>("itemtype"), 101);
	ASSERT_TRUE(inbox->next());
	EXPECT_EQ(inbox->getNumber<uint32_t>("sid"), 206);
	EXPECT_EQ(inbox->getNumber<uint32_t>("itemtype"), furnishingId);
	EXPECT_FALSE(inbox->next());
	EXPECT_FALSE(database.storeQuery("SELECT house_id FROM tile_store WHERE house_id=1"));
	EXPECT_TRUE(database.storeQuery("SELECT house_id FROM tile_store WHERE house_id=2"));
	EXPECT_FALSE(database.storeQuery("SELECT house_id FROM house_lists WHERE house_id=1"));
	EXPECT_TRUE(database.storeQuery("SELECT house_id FROM house_lists WHERE house_id=2"));
	EXPECT_FALSE(database.storeQuery("SELECT value FROM server_config WHERE config='house:depot:1'"));
}

TEST_F(HouseAuctionSettlement, StartupFurnitureWriteFailurePreservesSourceAndObligation) {
	ASSERT_NO_FATAL_FAILURE(prepareFurnitureTransfer());
	ASSERT_TRUE(database.executeQuery("ALTER TABLE player_inboxitems ADD CHECK (sid <= 205)"));
	EXPECT_THROW(IOMapSerialize::completeStartupHouseDepotTransfers(houses), std::runtime_error);
	EXPECT_TRUE(database.storeQuery("SELECT house_id FROM tile_store WHERE house_id=1"));
	EXPECT_TRUE(database.storeQuery("SELECT house_id FROM house_lists WHERE house_id=1"));
	EXPECT_TRUE(database.storeQuery("SELECT value FROM server_config WHERE config='house:depot:1'"));
	EXPECT_FALSE(database.storeQuery("SELECT sid FROM player_inboxitems WHERE sid>205"));
}
