/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "server/signals.hpp"

#include "config/configmanager.hpp"
#include "creatures/appearance/mounts/mounts.hpp"
#include "creatures/interactions/chat.hpp"
#include "game/game.hpp"
#include "game/scheduling/dispatcher.hpp"
#include "game/scheduling/save_manager.hpp"
#include "lua/creature/events.hpp"
#include "lua/global/globalevent.hpp"
#include "lua/scripts/lua_environment.hpp"
#include "lib/di/container.hpp"

Signals::Signals(asio::io_service &service) :
	set(service) {
	set.add(SIGINT);
	set.add(SIGTERM);
#ifndef _WIN32
	set.add(SIGUSR1);
	set.add(SIGHUP);
#else
	set.add(SIGBREAK);
#endif

	asyncWait();
}

void Signals::asyncWait() {
	set.async_wait([this](std::error_code err, int signal) {
		if (err) {
			g_logger().error("[Signals::asyncWait] - "
			                 "Signal handling error: {}",
			                 err.message());
			return;
		}
		dispatchSignalHandler(signal);
		asyncWait();
	});
}

void Signals::dispatchSignalHandler(int signal) {
	if (g_game().getGameState() == GAME_STATE_SHUTDOWN && signal != SIGTERM && signal != SIGINT
#ifdef _WIN32
		&& signal != SIGBREAK
#endif
	) {
		return;
	}

	switch (signal) {
		case SIGINT: // Shuts the server down
			g_dispatcher().addEvent(sigintHandler, __FUNCTION__);
			break;
		case SIGTERM: // Shuts the server down
			g_dispatcher().addEvent(sigtermHandler, __FUNCTION__);
			break;
#ifndef _WIN32
		case SIGHUP: // Reload config/data
			g_dispatcher().addEvent(sighupHandler, __FUNCTION__);
			break;
		case SIGUSR1: // Saves game state
			g_dispatcher().addEvent(sigusr1Handler, __FUNCTION__);
			break;
#else
		case SIGBREAK: // Shuts the server down
			g_dispatcher().addEvent(sigbreakHandler, __FUNCTION__);
			break;
#endif
		default:
			break;
	}
}

void Signals::sigbreakHandler() {
	// Dispatcher thread
	g_logger().info("SIGBREAK received, shutting game server down...");
	g_game().setGameState(GAME_STATE_SHUTDOWN);
}

void Signals::sigtermHandler() {
	// Dispatcher thread
	g_logger().info("SIGTERM received, shutting game server down...");
	g_game().setGameState(GAME_STATE_SHUTDOWN);
}

void Signals::sigusr1Handler() {
	// Dispatcher thread
	g_logger().info("SIGUSR1 received, saving the game state...");
	g_globalEvents().save();
	g_saveManager().scheduleAll();
}

void Signals::sighupHandler() {
	// Dispatcher thread
	g_logger().info("SIGHUP received, reloading config files...");

	g_configManager().reload();
	g_logger().info("Reloaded config");

	g_game().raids.reload();
	g_game().raids.startup();
	g_logger().info("Reloaded raids");

	Item::items.reload();
	g_logger().info("Reloaded items");

	g_game().mounts->reload();
	g_logger().info("Reloaded mounts");

	g_events().loadFromXml();
	g_logger().info("Reloaded events");

	g_chat().load();
	g_logger().info("Reloaded chatchannels");

	g_luaEnvironment().loadFile(g_configManager().getString(CORE_DIRECTORY) + "/core.lua", "core.lua");
	g_logger().info("Reloaded core.lua");

	lua_gc(g_luaEnvironment().getLuaState(), LUA_GCCOLLECT, 0);
}

void Signals::sigintHandler() {
	// Dispatcher thread
	g_logger().info("SIGINT received, shutting game server down...");
	g_game().setGameState(GAME_STATE_SHUTDOWN);
}
