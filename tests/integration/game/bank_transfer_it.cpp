#include "creatures/players/grouping/guild.hpp"
#include "creatures/players/player.hpp"
#include "database/database.hpp"
#include "game/bank/bank.hpp"
#include "io/iomarket.hpp"
#include "map/town.hpp"

#include <gtest/gtest.h>

namespace {
class BankTransfer : public testing::Test {
protected:
	Database &database = g_database();

	void SetUp() override {
		ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE players (id INT PRIMARY KEY, balance BIGINT UNSIGNED) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE guilds (id INT PRIMARY KEY, balance BIGINT UNSIGNED CHECK (balance <= 200)) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE server_config (config VARCHAR(50) PRIMARY KEY, value VARCHAR(256) NOT NULL) ENGINE=InnoDB"));
		ASSERT_TRUE(database.executeQuery("INSERT INTO players VALUES (1, 100)"));
		ASSERT_TRUE(database.executeQuery("INSERT INTO guilds VALUES (1, 40), (2, 195)"));
	}

	void TearDown() override {
		EXPECT_TRUE(database.executeQuery("DROP TEMPORARY TABLE IF EXISTS server_config, guilds, players"));
	}

	void expectBalance(const std::string &table, uint32_t id, uint64_t expected) {
		const auto row = database.storeQuery(fmt::format("SELECT balance FROM {} WHERE id={}", table, id));
		ASSERT_TRUE(row);
		EXPECT_EQ(row->getNumber<uint64_t>("balance"), expected);
	}

	static std::shared_ptr<Player> livePlayer() {
		const auto player = std::make_shared<Player>();
		player->setGUID(1);
		player->setOnline(true);
		player->setBankBalance(300);
		return player;
	}
};
}

TEST_F(BankTransfer, WritesLiveAndOfflineBalancesTogether) {
	const auto player = livePlayer();
	const auto guild = std::make_shared<Guild>(1, "Fixture Guild");
	guild->setBankBalance(5000);
	bool pending = true;
	{
		Bank source(player);
		const auto destination = std::make_shared<Bank>(guild);
		ASSERT_TRUE(source.transferTo(destination, 25, &pending));
	}
	EXPECT_FALSE(pending);
	expectBalance("players", 1, 275);
	expectBalance("guilds", 1, 65);
	EXPECT_EQ(player->getBankBalance(), 275);
	EXPECT_EQ(guild->getBankBalance(), 65);
}

TEST_F(BankTransfer, CreditsOfflinePlayerFromPersistedBalance) {
	ASSERT_TRUE(database.executeQuery("INSERT INTO players VALUES (2, 60)"));
	const auto town = std::make_shared<Town>(1);
	const auto from = livePlayer();
	from->setTown(town);
	const auto to = std::make_shared<Player>();
	to->setGUID(2);
	to->setTown(town);
	to->setOnline(false);
	to->setBankBalance(5000);
	Bank source(from);
	ASSERT_TRUE(source.transferTo(std::make_shared<Bank>(to), 10));
	expectBalance("players", 1, 290);
	expectBalance("players", 2, 70);
	EXPECT_EQ(to->getBankBalance(), 70);
}

TEST_F(BankTransfer, FailedCreditRollsBackDebitAndReceipt) {
	const auto player = livePlayer();
	const auto guild = std::make_shared<Guild>(2, "Fixture Guild");
	guild->setBankBalance(195);
	Bank source(player);
	const auto destination = std::make_shared<Bank>(guild);
	bool pending = true;
	EXPECT_FALSE(source.transferTo(destination, 10, &pending));
	EXPECT_FALSE(pending);
	expectBalance("players", 1, 100);
	expectBalance("guilds", 2, 195);
	EXPECT_EQ(player->getBankBalance(), 300);
	EXPECT_EQ(guild->getBankBalance(), 195);
	EXPECT_FALSE(database.storeQuery("SELECT value FROM server_config"));
}

TEST_F(BankTransfer, MovesGoldBetweenOfflineGuilds) {
	const auto from = std::make_shared<Guild>(2, "Sender");
	const auto to = std::make_shared<Guild>(1, "Receiver");
	Bank source(from);
	ASSERT_TRUE(source.transferTo(std::make_shared<Bank>(to), 5));
	expectBalance("guilds", 2, 190);
	expectBalance("guilds", 1, 45);
	EXPECT_EQ(from->getBankBalance(), 190);
	EXPECT_EQ(to->getBankBalance(), 45);
}

TEST_F(BankTransfer, BusyPlayerReturnsPendingWithoutChangingEitherBalance) {
	const auto player = livePlayer();
	const auto guild = std::make_shared<Guild>(1, "Fixture Guild");
	guild->setBankBalance(40);
	Bank source(player);
	const auto destination = std::make_shared<Bank>(guild);
	IOMarket::setPlayerFillPending(player->getGUID(), true);
	bool pending = false;
	EXPECT_FALSE(source.transferTo(destination, 10, &pending));
	IOMarket::setPlayerFillPending(player->getGUID(), false);
	EXPECT_TRUE(pending);
	expectBalance("players", 1, 100);
	expectBalance("guilds", 1, 40);
	EXPECT_EQ(player->getBankBalance(), 300);
	EXPECT_EQ(guild->getBankBalance(), 40);
}
