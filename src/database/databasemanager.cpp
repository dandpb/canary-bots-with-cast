/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "database/databasemanager.hpp"

#include "config/configmanager.hpp"
#include "lua/functions/core/libs/core_libs_functions.hpp"
#include "lua/scripts/luascript.hpp"

namespace InternalDBManager {
	int32_t extractVersionFromFilename(const std::string &filename) {
		std::regex versionRegex(R"((\d+)\.lua)");
		std::smatch match;

	if (std::regex_match(filename, match, versionRegex)) {
			return std::stoi(match.str(1));
		}

		return -1;
	}
}

bool DatabaseManager::optimizeTables() {
	Database &db = Database::getInstance();
	std::ostringstream query;

	query << "SELECT `TABLE_NAME` FROM `information_schema`.`TABLES` WHERE `TABLE_SCHEMA` = " << db.escapeString(g_configManager().getString(MYSQL_DB)) << " AND `DATA_FREE` > 0";
	DBResult_ptr result = db.storeQuery(query.str());
	if (!result) {
		return false;
	}

	do {
		std::string tableName = result->getString("TABLE_NAME");

		query.str(std::string());
		query << "OPTIMIZE TABLE `" << tableName << '`';

		std::string tableResult;
		if (db.executeQuery(query.str())) {
			tableResult = "[Success]";
		} else {
			tableResult = "[Failed]";
		}

		g_logger().info("Optimizing table {}... {}", tableName, tableResult);
	} while (result->next());

	return true;
}

bool DatabaseManager::tableExists(const std::string &tableName) {
	Database &db = Database::getInstance();

	std::ostringstream query;
	query << "SELECT `TABLE_NAME` FROM `information_schema`.`tables` WHERE `TABLE_SCHEMA` = DATABASE() AND `TABLE_NAME` = " << db.escapeString(tableName) << " LIMIT 1";
	return db.storeQuery(query.str()).get() != nullptr;
}

bool DatabaseManager::isDatabaseSetup() {
	Database &db = Database::getInstance();
	std::ostringstream query;
	query << "SELECT `TABLE_NAME` FROM `information_schema`.`tables` WHERE `TABLE_SCHEMA` = " << db.escapeString(g_configManager().getString(MYSQL_DB));
	return db.storeQuery(query.str()).get() != nullptr;
}

int32_t DatabaseManager::getDatabaseVersion() {
	if (!tableExists("server_config")) {
		Database &db = Database::getInstance();
		if (!db.executeQuery("CREATE TABLE `server_config` (`config` VARCHAR(50) NOT NULL, `value` VARCHAR(256) NOT NULL DEFAULT '', UNIQUE(`config`)) ENGINE = InnoDB")
			|| !registerDatabaseConfig("db_version", 0)) return -1;
		return 0;
	}

	int32_t version = 0;
	if (getDatabaseConfig("db_version", version)) {
		return version;
	}
	return -1;
}

bool DatabaseManager::updateDatabase(const std::filesystem::path &migrationDirectory) {
	Benchmark bm;
	const std::unique_ptr<lua_State, decltype(&lua_close)> state(luaL_newstate(), lua_close);
	if (!state) {
		return false;
	}
	auto* L = state.get();

	luaL_openlibs(L);
	CoreLibsFunctions::init(L);

	int32_t currentVersion = getDatabaseVersion();
	if (currentVersion < 0) return false;
	std::error_code directoryError;
	if (!std::filesystem::is_directory(migrationDirectory, directoryError)) {
		g_logger().error("Database migration directory is unavailable: {}", migrationDirectory.string());
		return false;
	}

	std::vector<std::pair<int32_t, std::string>> migrations;

	for (const auto &entry : std::filesystem::directory_iterator(migrationDirectory)) {
		if (entry.is_regular_file()) {
			std::string filename = entry.path().filename().string();
			int32_t fileVersion = InternalDBManager::extractVersionFromFilename(filename);
			if (fileVersion >= 0) migrations.emplace_back(fileVersion, entry.path().string());
		}
	}

	std::sort(migrations.begin(), migrations.end());

	for (const auto &[fileVersion, scriptPath] : migrations) {
		if (fileVersion > currentVersion) {
			if (!LuaScriptInterface::reserveScriptEnv()) {
				return false;
			}

			lua_pushnil(L);
			lua_setglobal(L, "onUpdateDatabase");
			if (luaL_dofile(L, scriptPath.c_str()) != 0) {
				const auto* error = lua_tostring(L, -1);
				g_logger().error("Could not load database migration {}: {}", fileVersion, error ? error : "unknown Lua error");
				LuaScriptInterface::resetScriptEnv();
				return false;
			}

			lua_getglobal(L, "onUpdateDatabase");
			if (!lua_isfunction(L, -1)) {
				LuaScriptInterface::resetScriptEnv();
				g_logger().error("Database migration {} does not define onUpdateDatabase", fileVersion);
				return false;
			}
			if (lua_pcall(L, 0, 1, 0) != 0) {
				LuaScriptInterface::resetScriptEnv();
				const auto* error = lua_tostring(L, -1);
				g_logger().error("Database migration {} failed: {}", fileVersion, error ? error : "unknown Lua error");
				return false;
			}

			const bool refused = lua_isboolean(L, -1) && !lua_toboolean(L, -1);
			lua_pop(L, 1);
			LuaScriptInterface::resetScriptEnv();
			if (refused || !registerDatabaseConfig("db_version", fileVersion)) {
				g_logger().error("Could not confirm database migration {}", fileVersion);
				return false;
			}
			currentVersion = fileVersion;
			g_logger().info("Database has been updated to version {}", currentVersion);
		}
	}

	double duration = bm.duration();
	if (duration < 1000.0) {
		g_logger().debug("Database update completed in {:.2f} ms", duration);
	} else {
		g_logger().debug("Database update completed in {:.2f} seconds", duration / 1000.0);
	}
	return true;
}

bool DatabaseManager::getDatabaseConfig(const std::string &config, int32_t &value) {
	Database &db = Database::getInstance();
	std::ostringstream query;
	query << "SELECT `value` FROM `server_config` WHERE `config` = " << db.escapeString(config);

	DBResult_ptr result = db.storeQuery(query.str());
	if (!result) {
		return false;
	}

	value = result->getNumber<int32_t>("value");
	return true;
}

bool DatabaseManager::registerDatabaseConfig(const std::string &config, int32_t value) {
	auto &database = g_database();
	return database.executeQuery(fmt::format(
		"INSERT INTO `server_config` (`config`, `value`) VALUES ({}, '{}') ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)",
		database.escapeString(config), value));
}
