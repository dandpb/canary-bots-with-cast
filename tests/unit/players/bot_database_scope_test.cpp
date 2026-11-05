#include <gtest/gtest.h>
#include "database/database.hpp"

TEST(BotDatabaseScope, NestedConnectionsAndExceptionsRestoreThePreviousRoute) {
	Database outer;
	Database inner;
	Database::ScopedConnection route(outer);
	EXPECT_EQ(&Database::getInstance(), &outer);
	try {
		Database::ScopedConnection nested(inner);
		EXPECT_EQ(&Database::getInstance(), &inner);
		throw std::runtime_error("fixture");
	} catch (const std::runtime_error&) {}
	EXPECT_EQ(&Database::getInstance(), &outer);
}

TEST(BotDatabaseScope, RoutingIsLocalToTheSaveWorkerThread) {
	Database outer;
	Database inner;
	Database::ScopedConnection route(outer);
	std::thread worker([&] {
		Database::ScopedConnection nested(inner);
		EXPECT_EQ(&Database::getInstance(), &inner);
	});
	worker.join();
	EXPECT_EQ(&Database::getInstance(), &outer);
}

TEST(BotDatabaseScope, CheckpointCaptureNeedsNoConnectionAndRejectsReads) {
	std::vector<std::string> statements;
	Database sink;
	sink.collectStatements(statements);
	Database::ScopedConnection route(sink);
	const std::string bytes("\0'\\\xff", 4);
	EXPECT_EQ(sink.escapeBlob(bytes.data(), bytes.size()), "X'00275CFF'");
	EXPECT_EQ(sink.escapeString(""), "X''");
	EXPECT_TRUE(sink.executeQuery("UPDATE fixture SET value=1"));
	EXPECT_EQ(statements, (std::vector<std::string> {"UPDATE fixture SET value=1"}));
	EXPECT_THROW(sink.storeQuery("SELECT 1"), std::logic_error);
}
