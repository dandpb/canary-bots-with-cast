/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (C) 2019-present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 */

#pragma once

#include "creatures/players/bot/bot_engine_interface.hpp"

class BotEngineLoader {
public:
	static BotEngineLoader& getInstance();

	// Load the shared library for the first time
	bool load(const std::string& soPath = "./libbot_engine.so");
	bool initialize();

	bool prepareReload();
	bool commitReload(uint64_t ticket);
	void cancelReload(uint64_t ticket);
	uint64_t preparedTicket() const { return preparedTicket_; }
	const std::string& lastError() const { return lastError_; }
	const std::string& phase() const { return phase_; }
	IBotEngine* tryGetEngine() const;
	// Convenience for native callers: prepare, then commit the same candidate.
	bool reload();

	// Internal reference accessor; optional consumers must use tryGetEngine()
	IBotEngine& getEngine();

	// Check if .so is loaded and engine is valid
	bool isLoaded() const;

	// Clean shutdown
	void unload();

	BotEngineLoader(const BotEngineLoader&) = delete;
	BotEngineLoader& operator=(const BotEngineLoader&) = delete;

private:
	struct Module;
	BotEngineLoader();
	~BotEngineLoader();

	std::unique_ptr<Module> prepare(const std::string& path);
	bool fail(const std::string& phase, const std::string& message);
	std::unique_ptr<Module> active_;
	std::unique_ptr<Module> prepared_;
	std::string soPath_ = "./libbot_engine.so";
	std::string lastError_;
	std::string phase_ = "idle";
	uint64_t nextTicket_ = 0;
	uint64_t preparedTicket_ = 0;
};
