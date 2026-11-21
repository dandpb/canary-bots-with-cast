#include "database/database.hpp"
#include "io/iostoreorders.hpp"
#include "lua/functions/core/libs/db_functions.hpp"

#include <gtest/gtest.h>

namespace {
	class StoreOrder : public testing::Test {
	protected:
		Database &database = g_database();

		void SetUp() override {
			const auto schema = database.storeQuery("SHOW CREATE TABLE store_orders");
			ASSERT_TRUE(schema);
			auto createOrders = schema->getString("Create Table");
			ASSERT_TRUE(createOrders.starts_with("CREATE TABLE "));
			createOrders.insert(7, "TEMPORARY ");
			ASSERT_TRUE(database.executeQuery(createOrders));
			ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE accounts (id INT UNSIGNED PRIMARY KEY, coins INT UNSIGNED, coins_transferable INT UNSIGNED) ENGINE=InnoDB"));
			ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE players (id INT PRIMARY KEY, account_id INT UNSIGNED, save INT UNSIGNED) ENGINE=InnoDB"));
			ASSERT_TRUE(database.executeQuery(
				"CREATE TEMPORARY TABLE coins_transactions (account_id INT UNSIGNED, type INT UNSIGNED, coin_type INT UNSIGNED, "
				"amount INT UNSIGNED, description VARCHAR(3500), CHECK (amount <> 13)) ENGINE=InnoDB"
			));
			ASSERT_TRUE(database.executeQuery("INSERT INTO accounts VALUES (1, 100, 200), (2, 400, 500)"));
			ASSERT_TRUE(database.executeQuery("INSERT INTO players VALUES (101, 1, 1), (102, 1, 1), (103, 1, 0), (201, 2, 1)"));
		}

		void TearDown() override {
			EXPECT_TRUE(database.executeQuery("DROP TEMPORARY TABLE IF EXISTS coins_transactions, players, accounts, store_orders"));
		}

		void expectWallet(uint32_t normal, uint32_t transferable) {
			const auto row = database.storeQuery("SELECT coins, coins_transferable FROM accounts WHERE id = 1");
			ASSERT_TRUE(row);
			EXPECT_EQ(row->getNumber<uint32_t>("coins"), normal);
			EXPECT_EQ(row->getNumber<uint32_t>("coins_transferable"), transferable);
		}
	};
}

TEST_F(StoreOrder, FailedLedgerAndInvalidOwnerLeaveWalletAndOrdersUnchanged) {
	EXPECT_STREQ(IOStoreOrders::reserve(101, 1, 17, false, 13, "Ledger constraint").status, "refused");
	ASSERT_TRUE(database.executeQuery("ALTER TABLE store_orders ADD CHECK (offer_id <> 19)"));
	EXPECT_STREQ(IOStoreOrders::reserve(101, 1, 19, false, 7, "Order constraint").status, "refused");
	EXPECT_STREQ(IOStoreOrders::reserve(201, 1, 17, false, 7, "Wrong account").status, "refused");
	EXPECT_STREQ(IOStoreOrders::reserve(103, 1, 17, false, 7, "Unsaveable character").status, "refused");
	expectWallet(100, 200);
	EXPECT_FALSE(database.storeQuery("SELECT id FROM store_orders"));
	EXPECT_FALSE(database.storeQuery("SELECT amount FROM coins_transactions"));
}

TEST_F(StoreOrder, AccountCanClaimOneOrderAndRefundTheOriginalWalletOnce) {
	const auto reserved = IOStoreOrders::reserve(101, 1, 17, true, 40, "Offer paid with transferable coins");
	ASSERT_STREQ(reserved.status, "reserved");
	ASSERT_NE(reserved.id, 0);
	const auto pending = IOStoreOrders::reserve(102, 1, 18, false, 20, "Second character on the same account");
	EXPECT_STREQ(pending.status, "pending");
	EXPECT_EQ(pending.id, reserved.id);
	EXPECT_FALSE(IOStoreOrders::claim(reserved.id, 102));
	EXPECT_TRUE(IOStoreOrders::claim(reserved.id, 101));
	EXPECT_FALSE(IOStoreOrders::claim(reserved.id, 101));
	const auto order = IOStoreOrders::get(reserved.id);
	ASSERT_TRUE(order);
	EXPECT_EQ(order->state, "delivering");
	EXPECT_FALSE(IOStoreOrders::finish(reserved.id, 101));
	expectWallet(100, 160);

	EXPECT_STREQ(IOStoreOrders::resolve(reserved.id, true), "refunded");
	EXPECT_STREQ(IOStoreOrders::resolve(reserved.id, true), "refunded");
	EXPECT_STREQ(IOStoreOrders::resolve(reserved.id, false), "refused");
	expectWallet(100, 200);
	const auto ledger = database.storeQuery("SELECT COUNT(*) AS n FROM coins_transactions WHERE account_id = 1 AND coin_type = 3 AND amount = 40");
	ASSERT_TRUE(ledger);
	EXPECT_EQ(ledger->getNumber<uint32_t>("n"), 2);
}

TEST_F(StoreOrder, FreeOrdersStillRequireClaimAndPreserveExactLuaIds) {
	ASSERT_TRUE(database.executeQuery("ALTER TABLE store_orders AUTO_INCREMENT = 9007199254740993"));
	const auto reserved = IOStoreOrders::reserve(101, 1, 17, false, 0, "Approved free purchase");
	ASSERT_STREQ(reserved.status, "reserved");
	ASSERT_EQ(reserved.id, 9007199254740993ULL);
	EXPECT_STREQ(IOStoreOrders::resolve(reserved.id, false), "refused");
	EXPECT_TRUE(IOStoreOrders::claim(reserved.id, 101));
	EXPECT_STREQ(IOStoreOrders::resolve(reserved.id, false), "complete");
	EXPECT_STREQ(IOStoreOrders::resolve(reserved.id, false), "complete");
	EXPECT_STREQ(IOStoreOrders::resolve(reserved.id, true), "refused");
	EXPECT_STREQ(IOStoreOrders::reserve(102, 1, 18, false, 0, "Second approved purchase").status, "reserved");
	expectWallet(100, 200);
	EXPECT_FALSE(database.storeQuery("SELECT amount FROM coins_transactions"));

	const std::unique_ptr<lua_State, decltype(&lua_close)> state(luaL_newstate(), lua_close);
	ASSERT_TRUE(state);
	luaL_openlibs(state.get());
	DBFunctions::init(state.get());
	ASSERT_EQ(luaL_dostring(state.get(),
		"local id = '9007199254740993'; local order = db.getStoreOrder(id); "
		"assert(order.id == id and order.state == 'complete' and order.amount == 0 and order.transferable == false); "
		"assert(db.getStoreOrder(9007199254740993) == nil)"), 0) << lua_tostring(state.get(), -1);
}
