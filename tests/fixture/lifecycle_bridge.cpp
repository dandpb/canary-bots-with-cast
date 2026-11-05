// Test-only Lua module for the labelled disposable lifecycle server. Not linked
// into the product or copied into normal runtime images.
#include "pch.hpp"
#include "creatures/players/bot/bot_engine_loader.hpp"
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
}

extern "C" int luaopen_lifecycle_bridge(lua_State* state) {
	lua_newtable(state);
	for (const auto& [name, function] : std::initializer_list<std::pair<const char*, lua_CFunction>> {
		{"setVirtual", setVirtual}, {"unregister", unregister}, {"pending", pending},
		{"armPause", armPause}, {"counts", counts}}) {
		lua_pushcfunction(state, function);
		lua_setfield(state, -2, name);
	}
	return 1;
}
