// Test-only Lua module for the labelled disposable lifecycle server. Not linked
// into the product or copied into normal runtime images.
#include "pch.hpp"
#include "creatures/players/bot/bot_engine_loader.hpp"
#include "creatures/players/player.hpp"
#include "game/scheduling/save_manager.hpp"
#include "game/scheduling/dispatcher.hpp"
extern "C" {
#include <lua.h>
#include <lauxlib.h>
}

namespace {
std::atomic<int> fired {0};
std::atomic<int> destroyed {0};
struct Marker { ~Marker() { ++destroyed; } };

IBotEngine* engine(lua_State* state) {
	auto* result = BotEngineLoader::getInstance().tryGetEngine();
	if (!result) luaL_error(state, "engine unavailable");
	return result;
}

int setVirtual(lua_State* state) {
	auto* bot = engine(state)->getBotState(luaL_checkinteger(state, 1));
	if (!bot || !bot->hibernated) return luaL_error(state, "hibernated fixture required");
	bot->currentPos = Position(luaL_checkinteger(state, 2), luaL_checkinteger(state, 3), luaL_checkinteger(state, 4));
	lua_pushboolean(state, true);
	return 1;
}

int unregister(lua_State* state) {
	engine(state)->unregisterBot(luaL_checkinteger(state, 1));
	lua_pushboolean(state, true);
	return 1;
}

int pending(lua_State* state) {
	lua_pushboolean(state, bool(g_saveManager().getPendingBotPlayer(luaL_checkinteger(state, 1))));
	return 1;
}

int armPause(lua_State* state) {
	auto* bot = engine(state)->getBotState(luaL_checkinteger(state, 1));
	if (!bot) return luaL_error(state, "registered fixture required");
	if (bot->pendingWalkPauseEventId) g_dispatcher().stopEvent(bot->pendingWalkPauseEventId);
	auto marker = std::make_shared<Marker>();
	bot->pendingWalkPauseEventId = g_dispatcher().scheduleEvent(luaL_checkinteger(state, 2),
		[marker] { ++fired; }, "qa_pending_walk");
	lua_pushboolean(state, true);
	return 1;
}

int counts(lua_State* state) {
	lua_pushinteger(state, fired.load());
	lua_pushinteger(state, destroyed.load());
	return 2;
}

int roster(lua_State* state) {
	const auto snapshot = engine(state)->captureReloadState();
	lua_newtable(state);
	int index = 0;
	for (const auto& entry : snapshot.entries) {
		lua_newtable(state);
		lua_pushinteger(state, entry.guid); lua_setfield(state, -2, "guid");
		lua_pushboolean(state, entry.active); lua_setfield(state, -2, "active");
		lua_pushboolean(state, entry.hibernated); lua_setfield(state, -2, "hibernated");
		lua_pushboolean(state, entry.aiPaused); lua_setfield(state, -2, "paused");
		lua_pushinteger(state, entry.player ? entry.player->getID() : 0); lua_setfield(state, -2, "runtimeId");
		lua_pushinteger(state, entry.position.x); lua_setfield(state, -2, "x");
		lua_pushinteger(state, entry.position.y); lua_setfield(state, -2, "y");
		lua_rawseti(state, -2, ++index);
	}
	return 1;
}
}

extern "C" int luaopen_lifecycle_bridge(lua_State* state) {
	lua_newtable(state);
	for (const auto& [name, function] : std::initializer_list<std::pair<const char*, lua_CFunction>> {
		{"setVirtual", setVirtual}, {"unregister", unregister}, {"pending", pending},
		{"armPause", armPause}, {"counts", counts}, {"roster", roster}}) {
		lua_pushcfunction(state, function);
		lua_setfield(state, -2, name);
	}
	return 1;
}
