/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (C) 2019-present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 */

#include "creatures/players/bot/bot_engine_loader.hpp"
#include "creatures/players/bot/bot_engine_abi.hpp"
#include "lib/logging/logger.hpp"

#include <dlfcn.h>
#include <filesystem>
#include <stdexcept>
#include <unistd.h>

struct BotEngineLoader::Module {
	using DestroyFunc = void (*)(IBotEngine*);
	void* handle = nullptr;
	IBotEngine* engine = nullptr;
	DestroyFunc destroy = nullptr;
	std::string directory;
	std::string path;
	~Module() {
		// Every exit follows the same order: instance, handle, private snapshot.
		if (engine && destroy) destroy(engine);
		if (handle) dlclose(handle);
		std::error_code ec;
		if (!path.empty()) std::filesystem::remove(path, ec);
		if (!directory.empty()) std::filesystem::remove(directory, ec);
	}
};

BotEngineLoader::BotEngineLoader() = default;
BotEngineLoader::~BotEngineLoader() = default;

BotEngineLoader& BotEngineLoader::getInstance() {
	static BotEngineLoader instance;
	return instance;
}

bool BotEngineLoader::fail(const std::string& phase, const std::string& message) {
	phase_ = phase;
	lastError_ = message;
	g_logger().error("[BotEngineLoader] phase={} failed: {}", phase, message);
	return false;
}

std::unique_ptr<BotEngineLoader::Module> BotEngineLoader::prepare(const std::string& path) {
	auto module = std::make_unique<Module>();
	try {
		// Exclusive directory; never fall back to opening the mutable source path.
		std::string pattern = path + ".reload-XXXXXX";
		if (!mkdtemp(pattern.data())) {
			fail("snapshot", "cannot reserve a private library snapshot directory");
			return nullptr;
		}
		module->directory = pattern;
		module->path = pattern + "/engine.so";
		std::filesystem::copy_file(path, module->path);
		std::filesystem::permissions(module->path, std::filesystem::perms::owner_read);
		module->handle = dlopen(module->path.c_str(), RTLD_NOW | RTLD_LOCAL);
		if (!module->handle) {
			fail("open", dlerror());
			return nullptr;
		}
		auto abi = reinterpret_cast<BotEngineAbiFunc>(dlsym(module->handle, "botEngineAbiTag"));
		if (!abi || !abi() || std::string_view(abi()) != BOT_ENGINE_ABI_TAG) {
			fail("abi", "missing or incompatible ABI; rebuild server and library together");
			return nullptr;
		}
		using CreateFunc = IBotEngine* (*)();
		auto create = reinterpret_cast<CreateFunc>(dlsym(module->handle, "createBotEngine"));
		module->destroy = reinterpret_cast<Module::DestroyFunc>(dlsym(module->handle, "destroyBotEngine"));
		auto prepareData = reinterpret_cast<PrepareBotEngineFunc>(dlsym(module->handle, "prepareBotEngine"));
		if (!create || !module->destroy || !prepareData) {
			fail("symbols", "missing factory, destructor or authored-data preparation export");
			return nullptr;
		}
		module->engine = create();
		if (!module->engine) {
			fail("factory", "createBotEngine returned null");
			return nullptr;
		}
		char error[2048] = {};
		if (!prepareData(module->engine, error, sizeof(error))) {
			error[sizeof(error) - 1] = '\0';
			fail("data", error[0] ? error : "candidate authored-data preparation failed");
			return nullptr;
		}
	} catch (const std::exception& exception) {
		fail("prepare", exception.what());
		return nullptr;
	} catch (...) {
		fail("prepare", "unexpected exception preparing candidate");
		return nullptr;
	}
	return module;
}

bool BotEngineLoader::load(const std::string& soPath) {
	if (active_ || prepared_) return fail("load", "engine already loaded or candidate pending");
	soPath_ = soPath;
	active_ = prepare(soPath_);
	if (!active_) return false;
	lastError_.clear();
	phase_ = "loaded";
	return true;
}

bool BotEngineLoader::prepareReload() {
	if (prepared_) return fail("prepare", "another candidate is already pending");
	prepared_ = prepare(soPath_);
	if (!prepared_) return false;
	preparedTicket_ = ++nextTicket_;
	lastError_.clear();
	phase_ = "prepared";
	g_logger().info("[BotEngineLoader] phase=prepared ticket={}", preparedTicket_);
	return true;
}

bool BotEngineLoader::initialize() {
	if (!isLoaded()) return fail("initialize", "bot engine unavailable");
	std::string error;
	bool success = true;
	try {
		getEngine().loadHuntData();
	} catch (const std::exception& exception) {
		success = false;
		error = exception.what();
	} catch (...) {
		success = false;
		error = "unexpected candidate initialization failure";
	}
	// The caught exception can have a destructor in the candidate's library.
	// Leave the handler (and destroy that exception) before closing its module.
	if (!success) {
		unload();
		return fail("initialize", error.empty() ? "candidate initialization failed" : error);
	}
	phase_ = "initialized";
	return true;
}

bool BotEngineLoader::commitReload(uint64_t ticket) {
	if (!prepared_ || ticket == 0 || ticket != preparedTicket_) {
		return fail("commit", "missing or stale prepared candidate ticket");
	}
	// #12/B supplies the complete Player handoff from #11 at this boundary.
	active_.reset();
	active_ = std::move(prepared_);
	preparedTicket_ = 0;
	lastError_.clear();
	phase_ = "committed";
	g_logger().info("[BotEngineLoader] phase=committed ticket={}", ticket);
	return true;
}

void BotEngineLoader::cancelReload(uint64_t ticket) {
	if (ticket != 0 && ticket == preparedTicket_) {
		prepared_.reset();
		preparedTicket_ = 0;
	}
}

bool BotEngineLoader::reload() { return prepareReload() && commitReload(preparedTicket_); }
IBotEngine* BotEngineLoader::tryGetEngine() const { return active_ ? active_->engine : nullptr; }
IBotEngine& BotEngineLoader::getEngine() {
	auto* engine = tryGetEngine();
	if (!engine) throw std::logic_error("bot engine unavailable: use tryGetEngine for optional behavior");
	return *engine;
}
bool BotEngineLoader::isLoaded() const { return tryGetEngine() != nullptr; }
void BotEngineLoader::unload() {
	prepared_.reset();
	preparedTicket_ = 0;
	active_.reset();
}
IBotEngine& getBotEngineInstance() { return BotEngineLoader::getInstance().getEngine(); }
IBotEngine* getBotEngineIfLoaded() { return BotEngineLoader::getInstance().tryGetEngine(); }
