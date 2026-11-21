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

#include <filesystem>

class DatabaseManager {
public:
	static bool tableExists(const std::string &table);

	static int32_t getDatabaseVersion();
	static bool isDatabaseSetup();

	static bool optimizeTables();
	static bool updateDatabase(const std::filesystem::path &migrationDirectory);

	static bool getDatabaseConfig(const std::string &config, int32_t &value);
	static bool registerDatabaseConfig(const std::string &config, int32_t value);
};
