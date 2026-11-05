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
