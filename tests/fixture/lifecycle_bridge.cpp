// Test-only Lua module for the labelled disposable lifecycle server. Not linked
// into the product or copied into normal runtime images.
#include "pch.hpp"
#include "creatures/players/bot/bot_engine_loader.hpp"
#include "creatures/players/player.hpp"
#include "game/scheduling/save_manager.hpp"
#include "game/scheduling/dispatcher.hpp"
#include "utils/tools.hpp"
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

// Seed only a state-machine boundary; transitions still run through production tick().
int reloadProgress(lua_State* state) {
	auto* current = engine(state);
	const auto guid = static_cast<uint32_t>(luaL_checkinteger(state, 1));
	const std::string operation = luaL_checkstring(state, 2);
	auto* bot = current->getBotState(guid);
	if (!bot || !bot->getPlayer()) return luaL_error(state, "awake reload fixture required");
	if (operation == "sourceTown") {
		// The fixture avatar is stationary; select a town with an authored boat
		// so startTravel does not choose Dawnport's unrelated recovery route.
		bot->townId = 8;
		bot->townName = "Thais";
	} else if (operation == "questProgress" || operation == "regularCollision") {
		bot->state = BotAIState::HUNTING;
		bot->huntPhase = HuntPhase::PATROLLING;
		if (operation == "regularCollision") bot->huntScriptId = 1;
		bot->huntWaypointIdx = guid == 65001 ? 1 : 2;
		bot->huntKillCount = guid == 65001 ? 5 : 7;
		bot->huntStartTime = OTSYS_TIME() - 1000;
		bot->huntEndTime = OTSYS_TIME() + 300000;
	} else if (operation == "questCompleted") {
		// The journey is not simulated here: drive the real completion/reroll
		// boundary after the quest's return and supply steps have finished.
		bot->state = BotAIState::HUNTING;
		bot->huntPhase = HuntPhase::RESUPPLYING;
		bot->huntResupplyStart = OTSYS_TIME() - 1000;
		bot->prepareStartTime = OTSYS_TIME() - 1000;
		bot->prepareStep = 5;
		bot->resupplyRerolled = true;
	} else if (operation == "preparing" || operation == "resupplying") {
		bot->state = BotAIState::HUNTING;
		bot->huntPhase = operation == "preparing" ? HuntPhase::PREPARING : HuntPhase::RESUPPLYING;
		bot->prepareStartTime = OTSYS_TIME() - 1000;
		bot->prepareWaitUntil = OTSYS_TIME() + 5000;
		bot->prepareStep = 1;
		bot->prepareTarget = bot->getPlayer()->getPosition();
		bot->prepareHasTarget = false;
		bot->huntResupplyStart = OTSYS_TIME() - 500;
		bot->huntResupplyPhase = 1;
		bot->resupplyRerolled = false;
	} else if (operation == "unavailableHunt") {
		bot->state = BotAIState::TRAVELING;
		bot->huntScriptId = 0xFFFFFFFE;
		bot->pendingHuntAfterTravel = true;
		bot->travelPhase = "arrived";
	} else if (operation == "dwelling") {
		bot->state = BotAIState::DWELLING;
		bot->dwellUntil = OTSYS_TIME() + luaL_checkinteger(state, 3);
		bot->hasWalkTarget = false;
		bot->currentPOI = nullptr;
		bot->hasDepotTarget = false;
		bot->aiPaused = true;
	} else if (operation == "arrived") {
		if (bot->state != BotAIState::TRAVELING) return luaL_error(state, "traveling fixture required");
		bot->travelPhase = "arrived";
	} else if (operation == "tick") {
		bot->wakeQuietTicks = 0;
		bot->tickCounter = 29; // Next tick is due for travel (%2), preparation (%3) and dwell (%5).
		bot->aiPaused = false;
		current->tick();
		bot = current->getBotState(guid);
		if (!bot) return luaL_error(state, "fixture disappeared during tick");
		bot->aiPaused = true;
	} else if (operation != "inspect") return luaL_error(state, "unknown progress fixture operation");
	lua_newtable(state);
	lua_pushinteger(state, static_cast<int>(bot->state)); lua_setfield(state, -2, "state");
	lua_pushboolean(state, bot->pendingHuntAfterTravel); lua_setfield(state, -2, "pendingHuntAfterTravel");
	lua_pushinteger(state, bot->dwellUntil); lua_setfield(state, -2, "dwellUntil");
	lua_pushinteger(state, OTSYS_TIME()); lua_setfield(state, -2, "now");
	lua_pushinteger(state, bot->huntScriptId); lua_setfield(state, -2, "huntId");
	lua_pushboolean(state, bot->isQuestBot); lua_setfield(state, -2, "isQuestBot");
	lua_pushinteger(state, bot->huntWaypointIdx); lua_setfield(state, -2, "waypoint");
	lua_pushinteger(state, bot->huntKillCount); lua_setfield(state, -2, "kills");
	lua_pushinteger(state, static_cast<int>(bot->huntPhase)); lua_setfield(state, -2, "huntPhase");
	lua_pushinteger(state, bot->prepareStep); lua_setfield(state, -2, "prepareStep");
	lua_pushinteger(state, bot->prepareStartTime); lua_setfield(state, -2, "prepareStarted");
	lua_pushinteger(state, bot->prepareWaitUntil); lua_setfield(state, -2, "prepareWaitUntil");
	lua_pushinteger(state, bot->huntResupplyStart); lua_setfield(state, -2, "resupplyStarted");
	lua_pushinteger(state, bot->huntResupplyPhase); lua_setfield(state, -2, "resupplyPhase");
	lua_pushboolean(state, bot->resupplyRerolled); lua_setfield(state, -2, "resupplyRerolled");
	lua_pushinteger(state, bot->getPlayer() ? bot->getPlayer()->getID() : 0); lua_setfield(state, -2, "runtimeId");
	const auto reservations = current->executeCommand("_global", "whohunts");
	lua_pushlstring(state, reservations.data(), reservations.size()); lua_setfield(state, -2, "reservations");
	return 1;
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
		{"armPause", armPause}, {"counts", counts}, {"roster", roster}, {"reloadProgress", reloadProgress}}) {
		lua_pushcfunction(state, function);
		lua_setfield(state, -2, name);
	}
	return 1;
}
