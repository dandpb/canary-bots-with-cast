#include "database/database.hpp"
#include "database/databasemanager.hpp"

#include <gtest/gtest.h>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <future>

TEST(DatabaseTransaction, InsertQueryReturnsOnlyTheIdFromItsStatement) {
	auto &database = g_database();
	ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE insert_id_audit (id INT AUTO_INCREMENT PRIMARY KEY, value INT UNIQUE) ENGINE=InnoDB"));
	const auto firstId = database.insertQuery("INSERT INTO insert_id_audit (value) VALUES (4)");
	ASSERT_NE(firstId, 0);
	const auto secondId = database.insertQuery("INSERT INTO insert_id_audit (value) VALUES (6)");
	ASSERT_NE(secondId, 0);
	EXPECT_NE(firstId, secondId);
	EXPECT_EQ(database.insertQuery("INSERT INTO insert_id_audit (value) VALUES (6)"), 0);
	const auto updated = database.storeQuery("SELECT id, value FROM insert_id_audit ORDER BY value");
	ASSERT_TRUE(updated);
	EXPECT_EQ(updated->getNumber<uint64_t>("id"), firstId);
	ASSERT_TRUE(updated->next());
	EXPECT_EQ(updated->getNumber<uint64_t>("id"), secondId);
	EXPECT_TRUE(database.executeQuery("DROP TEMPORARY TABLE insert_id_audit"));
}

TEST(DatabaseTransaction, InsertQueryCannotCollectAStatementWithoutExecutingIt) {
	Database capture;
	std::vector<std::string> statements;
	capture.collectStatements(statements);
	EXPECT_EQ(capture.insertQuery("INSERT INTO insert_id_audit (value) VALUES (4)"), 0);
	EXPECT_TRUE(statements.empty());
}

TEST(DatabaseMigration, RefusalKeepsVersionAndBlocksLaterMigrationsUntilRetry) {
	auto &database = g_database();
	const auto directory = std::filesystem::temp_directory_path() / fmt::format("canary-migration-{}", std::chrono::steady_clock::now().time_since_epoch().count());
	struct Cleanup {
		std::filesystem::path directory;
		Database &database;
		~Cleanup() {
			std::error_code error;
			std::filesystem::remove_all(directory, error);
			database.executeQuery("DROP TEMPORARY TABLE IF EXISTS server_config");
		}
	} cleanup { directory, database };
	ASSERT_TRUE(std::filesystem::create_directory(directory));
	ASSERT_TRUE(database.executeQuery("CREATE TEMPORARY TABLE server_config (config VARCHAR(50) PRIMARY KEY, value VARCHAR(256) NOT NULL) ENGINE=InnoDB"));
	ASSERT_TRUE(DatabaseManager::registerDatabaseConfig("db_version", 56));
	std::ofstream(directory / "57.lua") << "function onUpdateDatabase() return false end\n";
	std::ofstream(directory / "58.lua") << "function onUpdateDatabase() assert(db.query([[INSERT INTO server_config VALUES ('migration_test', '1')]])) end\n";
	EXPECT_FALSE(DatabaseManager::updateDatabase(directory));
	EXPECT_EQ(DatabaseManager::getDatabaseVersion(), 56);
	int marker = 0;
	EXPECT_FALSE(DatabaseManager::getDatabaseConfig("migration_test", marker));

	std::ofstream(directory / "57.lua") << "function onUpdateDatabase() return true end\n";
	std::ofstream(directory / "58.lua") << "-- A loaded script must define its own callback.\n";
	EXPECT_FALSE(DatabaseManager::updateDatabase(directory));
	EXPECT_EQ(DatabaseManager::getDatabaseVersion(), 57);
	std::ofstream(directory / "58.lua") << "function onUpdateDatabase() assert(db.query([[INSERT INTO server_config VALUES ('migration_test', '1')]])) end\n";
	EXPECT_TRUE(DatabaseManager::updateDatabase(directory));
	EXPECT_EQ(DatabaseManager::getDatabaseVersion(), 58);
	EXPECT_TRUE(DatabaseManager::getDatabaseConfig("migration_test", marker));
	EXPECT_EQ(marker, 1);
}

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
