#include "database/database.hpp"

#include <gtest/gtest.h>
#include <chrono>
#include <future>

TEST(DatabaseTransaction, FalseCallbackRollsBackAllPreviousStatements) {
	auto &database = g_database();
	ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE transaction_audit (id INT PRIMARY KEY, value INT) ENGINE=InnoDB"));
	ASSERT_TRUE(database.executeQuery("INSERT INTO transaction_audit VALUES (1, 20), (2, 30)"));

	EXPECT_FALSE(DBTransaction::executeWithinTransaction([&] {
		if (!database.executeQuery("UPDATE transaction_audit SET value=99 WHERE id=1")) {
			return false;
		}
		return database.executeQuery("INSERT INTO transaction_audit VALUES (2, 90)");
	}));

	auto result = database.storeQuery("SELECT SUM(value) AS total FROM transaction_audit");
	ASSERT_TRUE(result);
	EXPECT_EQ(result->getNumber<int>("total"), 50);
	EXPECT_TRUE(database.executeQuery("DROP TEMPORARY TABLE transaction_audit"));
}

TEST(DatabaseTransaction, SecondCallerWaitsUntilFirstTransactionEnds) {
	auto &database = g_database();
	std::promise<void> enteredFirst;
	std::promise<void> enteredSecond;
	std::promise<void> releaseFirst;
	auto firstEntered = enteredFirst.get_future();
	auto secondEntered = enteredSecond.get_future();
	auto release = releaseFirst.get_future();
	auto first = std::async(std::launch::async, [&] {
		Database::ScopedConnection route(database);
		return DBTransaction::executeWithinTransaction([&] {
			enteredFirst.set_value();
			release.wait();
			return true;
		});
	});
	EXPECT_EQ(firstEntered.wait_for(std::chrono::seconds(1)), std::future_status::ready);
	auto second = std::async(std::launch::async, [&] {
		Database::ScopedConnection route(database);
		return DBTransaction::executeWithinTransaction([&] {
			enteredSecond.set_value();
			return true;
		});
	});
	EXPECT_EQ(secondEntered.wait_for(std::chrono::milliseconds(100)), std::future_status::timeout);
	releaseFirst.set_value();
	EXPECT_TRUE(first.get());
	EXPECT_TRUE(second.get());
	EXPECT_EQ(secondEntered.wait_for(std::chrono::seconds(0)), std::future_status::ready);
}

TEST(DatabaseTransaction, ReceiptRollsBackWithDataAndPreventsReplayingACommit) {
	auto &database = g_database();
	ASSERT_TRUE(database.executeQuery("DELETE FROM server_config WHERE config='save:test:receipt'"));
	ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE receipt_audit (value INT) ENGINE=InnoDB"));
	ASSERT_TRUE(database.executeQuery("INSERT INTO receipt_audit VALUES (0)"));
	{
		const DBTransaction::ScopedReceipt receipt("save:test:receipt", "first");
		EXPECT_FALSE(DBTransaction::executeWithinTransaction([&] {
			database.executeQuery("UPDATE receipt_audit SET value=99");
			return false;
		}));
		ASSERT_TRUE(DBTransaction::executeWithinTransaction([&] {
			return database.executeQuery("UPDATE receipt_audit SET value=value+1");
		}));
		EXPECT_TRUE(DBTransaction::executeWithinTransaction([] {
			ADD_FAILURE() << "A retry must leave committed data alone";
			return false;
		}));
	}
	{
		const DBTransaction::ScopedReceipt receipt("save:test:receipt", "second");
		ASSERT_TRUE(DBTransaction::executeWithinTransaction([&] {
			return database.executeQuery("UPDATE receipt_audit SET value=value+1");
		}));
	}
	const auto row = database.storeQuery("SELECT value FROM receipt_audit");
	ASSERT_TRUE(row);
	EXPECT_EQ(row->getNumber<int>("value"), 2);
	EXPECT_TRUE(database.executeQuery("DROP TEMPORARY TABLE receipt_audit"));
	EXPECT_TRUE(database.executeQuery("DELETE FROM server_config WHERE config='save:test:receipt'"));
}
