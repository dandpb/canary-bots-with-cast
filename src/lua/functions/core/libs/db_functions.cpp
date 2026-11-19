/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "lua/functions/core/libs/db_functions.hpp"

#include "database/botdatabasetasks.hpp"
#include "database/databasemanager.hpp"
#include "database/databasetasks.hpp"
#include "io/iostoreorders.hpp"
#include "lua/scripts/lua_environment.hpp"
#include "lua/functions/lua_functions_loader.hpp"

#include <charconv>
#include <cmath>
#include <limits>
#include <string_view>

namespace {
	std::optional<uint32_t> readStoreNumber(lua_State* L, int index) {
		if (lua_type(L, index) != LUA_TNUMBER) {
			return std::nullopt;
		}
		const auto value = lua_tonumber(L, index);
		if (!std::isfinite(value) || value < 0 || value > std::numeric_limits<uint32_t>::max() || std::trunc(value) != value) {
			return std::nullopt;
		}
		return static_cast<uint32_t>(value);
	}

	std::string_view readStoreString(lua_State* L, int index) {
		if (lua_type(L, index) != LUA_TSTRING) {
			return {};
		}
		size_t size = 0;
		const auto value = lua_tolstring(L, index, &size);
		return { value, size };
	}

	uint64_t readStoreOrderId(lua_State* L) {
		const auto input = readStoreString(L, 1);
		if (input.empty() || input.size() > 20 || input.front() == '0') {
			return 0;
		}
		uint64_t id = 0;
		const auto end = input.data() + input.size();
		const auto parsed = std::from_chars(input.data(), end, id);
		return parsed.ec == std::errc {} && parsed.ptr == end ? id : 0;
	}
}

void DBFunctions::init(lua_State* L) {
	Lua::registerTable(L, "db");
	Lua::registerMethod(L, "db", "query", DBFunctions::luaDatabaseExecute);
	Lua::registerMethod(L, "db", "asyncQuery", DBFunctions::luaDatabaseAsyncExecute);
	Lua::registerMethod(L, "db", "storeQuery", DBFunctions::luaDatabaseStoreQuery);
	Lua::registerMethod(L, "db", "asyncStoreQuery", DBFunctions::luaDatabaseAsyncStoreQuery);
	// Bundle 6 (2026-06-11): bot variants route to the dedicated BotDatabaseTasks
	// worker (own thread + own connection) instead of the shared pool — see
	// botdatabasetasks.hpp for the worker-theft rationale. Bot Lua only.
	Lua::registerMethod(L, "db", "botAsyncQuery", DBFunctions::luaDatabaseBotAsyncExecute);
	Lua::registerMethod(L, "db", "botAsyncStoreQuery", DBFunctions::luaDatabaseBotAsyncStoreQuery);
	Lua::registerMethod(L, "db", "escapeString", DBFunctions::luaDatabaseEscapeString);
	Lua::registerMethod(L, "db", "escapeBlob", DBFunctions::luaDatabaseEscapeBlob);
	Lua::registerMethod(L, "db", "insert", DBFunctions::luaDatabaseInsert);
	Lua::registerMethod(L, "db", "lastInsertId", DBFunctions::luaDatabaseLastInsertId);
	Lua::registerMethod(L, "db", "tableExists", DBFunctions::luaDatabaseTableExists);
	Lua::registerMethod(L, "db", "reserveStoreOrder", DBFunctions::luaDatabaseReserveStoreOrder);
	Lua::registerMethod(L, "db", "claimStoreOrder", DBFunctions::luaDatabaseClaimStoreOrder);
	Lua::registerMethod(L, "db", "finishStoreOrder", DBFunctions::luaDatabaseFinishStoreOrder);
	Lua::registerMethod(L, "db", "getStoreOrder", DBFunctions::luaDatabaseGetStoreOrder);
	Lua::registerMethod(L, "db", "resolveStoreOrder", DBFunctions::luaDatabaseResolveStoreOrder);
}

int DBFunctions::luaDatabaseReserveStoreOrder(lua_State* L) {
	const auto playerGuid = readStoreNumber(L, 1);
	const auto accountId = readStoreNumber(L, 2);
	const auto offerId = readStoreNumber(L, 3);
	const auto amount = readStoreNumber(L, 5);
	const auto detail = readStoreString(L, 6);
	IOStoreOrders::Reservation result;
	if (playerGuid && accountId && offerId && lua_type(L, 4) == LUA_TBOOLEAN && amount && !detail.empty() && detail.size() <= 255) {
		result = IOStoreOrders::reserve(*playerGuid, *accountId, *offerId, lua_toboolean(L, 4) != 0, *amount, std::string(detail));
	}
	if (result.id != 0) {
		Lua::pushString(L, std::to_string(result.id));
	} else {
		lua_pushnil(L);
	}
	lua_pushstring(L, result.status);
	return 2;
}

int DBFunctions::luaDatabaseClaimStoreOrder(lua_State* L) {
	const auto id = readStoreOrderId(L);
	const auto playerGuid = readStoreNumber(L, 2);
	Lua::pushBoolean(L, playerGuid && IOStoreOrders::claim(id, *playerGuid));
	return 1;
}

int DBFunctions::luaDatabaseFinishStoreOrder(lua_State* L) {
	const auto id = readStoreOrderId(L);
	const auto playerGuid = readStoreNumber(L, 2);
	Lua::pushBoolean(L, playerGuid && IOStoreOrders::finish(id, *playerGuid));
	return 1;
}

int DBFunctions::luaDatabaseGetStoreOrder(lua_State* L) {
	const auto order = IOStoreOrders::get(readStoreOrderId(L));
	if (!order) {
		lua_pushnil(L);
		return 1;
	}
	lua_createtable(L, 0, 8);
	Lua::setField(L, "id", std::to_string(order->id));
	Lua::setField(L, "playerGuid", order->playerGuid);
	Lua::setField(L, "accountId", order->accountId);
	Lua::setField(L, "offerId", order->offerId);
	Lua::pushBoolean(L, order->transferable);
	lua_setfield(L, -2, "transferable");
	Lua::setField(L, "amount", order->amount);
	Lua::setField(L, "detail", order->detail);
	Lua::setField(L, "state", order->state);
	return 1;
}

int DBFunctions::luaDatabaseResolveStoreOrder(lua_State* L) {
	const auto id = readStoreOrderId(L);
	const auto action = readStoreString(L, 2);
	const auto result = action == "complete" || action == "refund" ? IOStoreOrders::resolve(id, action == "refund") : "refused";
	lua_pushstring(L, result);
	return 1;
}

int DBFunctions::luaDatabaseExecute(lua_State* L) {
	Lua::pushBoolean(L, Database::getInstance().executeQuery(Lua::getString(L, -1)));
	return 1;
}

int DBFunctions::luaDatabaseAsyncExecute(lua_State* L) {
	std::function<void(DBResult_ptr, bool)> callback;
	if (lua_gettop(L) > 1) {
		int32_t ref = luaL_ref(L, LUA_REGISTRYINDEX);
		auto scriptId = Lua::getScriptEnv()->getScriptId();
		callback = [ref, scriptId](const DBResult_ptr &, bool success) {
			lua_State* luaState = g_luaEnvironment().getLuaState();
			if (!luaState) {
				return;
			}

			if (!Lua::reserveScriptEnv()) {
				luaL_unref(luaState, LUA_REGISTRYINDEX, ref);
				return;
			}

			lua_rawgeti(luaState, LUA_REGISTRYINDEX, ref);
			Lua::pushBoolean(luaState, success);
			const auto env = Lua::getScriptEnv();
			env->setScriptId(scriptId, &g_luaEnvironment());
			g_luaEnvironment().callFunction(1);

			luaL_unref(luaState, LUA_REGISTRYINDEX, ref);
		};
	}
	g_databaseTasks().execute(Lua::getString(L, -1), callback);
	return 0;
}

int DBFunctions::luaDatabaseBotAsyncExecute(lua_State* L) {
	// Mirror of luaDatabaseAsyncExecute targeting g_botDatabaseTasks() (bundle 6).
	std::function<void(DBResult_ptr, bool)> callback;
	if (lua_gettop(L) > 1) {
		int32_t ref = luaL_ref(L, LUA_REGISTRYINDEX);
		auto scriptId = Lua::getScriptEnv()->getScriptId();
		callback = [ref, scriptId](const DBResult_ptr &, bool success) {
			lua_State* luaState = g_luaEnvironment().getLuaState();
			if (!luaState) {
				return;
			}

			if (!Lua::reserveScriptEnv()) {
				luaL_unref(luaState, LUA_REGISTRYINDEX, ref);
				return;
			}

			lua_rawgeti(luaState, LUA_REGISTRYINDEX, ref);
			Lua::pushBoolean(luaState, success);
			const auto env = Lua::getScriptEnv();
			env->setScriptId(scriptId, &g_luaEnvironment());
			g_luaEnvironment().callFunction(1);

			luaL_unref(luaState, LUA_REGISTRYINDEX, ref);
		};
	}
	g_botDatabaseTasks().execute(Lua::getString(L, -1), callback);
	return 0;
}

int DBFunctions::luaDatabaseBotAsyncStoreQuery(lua_State* L) {
	// Mirror of luaDatabaseAsyncStoreQuery targeting g_botDatabaseTasks() (bundle 6).
	std::function<void(DBResult_ptr, bool)> callback;
	if (lua_gettop(L) > 1) {
		int32_t ref = luaL_ref(L, LUA_REGISTRYINDEX);
		auto scriptId = Lua::getScriptEnv()->getScriptId();
		callback = [ref, scriptId](const DBResult_ptr &result, bool) {
			lua_State* luaState = g_luaEnvironment().getLuaState();
			if (!luaState) {
				return;
			}

			if (!Lua::reserveScriptEnv()) {
				luaL_unref(luaState, LUA_REGISTRYINDEX, ref);
				return;
			}

			lua_rawgeti(luaState, LUA_REGISTRYINDEX, ref);
			if (result) {
				lua_pushnumber(luaState, ScriptEnvironment::addResult(result));
			} else {
				Lua::pushBoolean(luaState, false);
			}
			const auto env = Lua::getScriptEnv();
			env->setScriptId(scriptId, &g_luaEnvironment());
			g_luaEnvironment().callFunction(1);

			luaL_unref(luaState, LUA_REGISTRYINDEX, ref);
		};
	}
	g_botDatabaseTasks().store(Lua::getString(L, -1), callback);
	return 0;
}

int DBFunctions::luaDatabaseStoreQuery(lua_State* L) {
	if (const DBResult_ptr &res = Database::getInstance().storeQuery(Lua::getString(L, -1))) {
		lua_pushnumber(L, ScriptEnvironment::addResult(res));
	} else {
		Lua::pushBoolean(L, false);
	}
	return 1;
}

int DBFunctions::luaDatabaseAsyncStoreQuery(lua_State* L) {
	std::function<void(DBResult_ptr, bool)> callback;
	if (lua_gettop(L) > 1) {
		int32_t ref = luaL_ref(L, LUA_REGISTRYINDEX);
		auto scriptId = Lua::getScriptEnv()->getScriptId();
		callback = [ref, scriptId](const DBResult_ptr &result, bool) {
			lua_State* luaState = g_luaEnvironment().getLuaState();
			if (!luaState) {
				return;
			}

			if (!Lua::reserveScriptEnv()) {
				luaL_unref(luaState, LUA_REGISTRYINDEX, ref);
				return;
			}

			lua_rawgeti(luaState, LUA_REGISTRYINDEX, ref);
			if (result) {
				lua_pushnumber(luaState, ScriptEnvironment::addResult(result));
			} else {
				Lua::pushBoolean(luaState, false);
			}
			const auto env = Lua::getScriptEnv();
			env->setScriptId(scriptId, &g_luaEnvironment());
			g_luaEnvironment().callFunction(1);

			luaL_unref(luaState, LUA_REGISTRYINDEX, ref);
		};
	}
	g_databaseTasks().store(Lua::getString(L, -1), callback);
	return 0;
}

int DBFunctions::luaDatabaseEscapeString(lua_State* L) {
	Lua::pushString(L, Database::getInstance().escapeString(Lua::getString(L, -1)));
	return 1;
}

int DBFunctions::luaDatabaseEscapeBlob(lua_State* L) {
	const uint32_t length = Lua::getNumber<uint32_t>(L, 2);
	Lua::pushString(L, Database::getInstance().escapeBlob(Lua::getString(L, 1).c_str(), length));
	return 1;
}

int DBFunctions::luaDatabaseInsert(lua_State* L) {
	const auto id = Database::getInstance().insertQuery(Lua::getString(L, -1));
	if (id != 0) {
		lua_pushnumber(L, id);
	} else {
		lua_pushnil(L);
	}
	return 1;
}

int DBFunctions::luaDatabaseLastInsertId(lua_State* L) {
	lua_pushnumber(L, Database::getInstance().getLastInsertId());
	return 1;
}

int DBFunctions::luaDatabaseTableExists(lua_State* L) {
	Lua::pushBoolean(L, DatabaseManager::tableExists(Lua::getString(L, -1)));
	return 1;
}
