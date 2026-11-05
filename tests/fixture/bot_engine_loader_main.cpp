// Isolated loader regression. Uses the production loader and real IBotEngine.
#include "creatures/players/bot/bot_engine_loader.hpp"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>

// This loader-only fixture has no game/DB or Players. Live handoff is covered
// by lifecycle_qa; reject any attempt to substitute nonempty persistence here.
void checkpointBotReloadPlayers(const BotReloadSnapshot& snapshot) { assert(snapshot.entries.empty()); }

int main(int argc, char** argv) {
	assert(argc == 2);
	namespace fs = std::filesystem;
	const fs::path root = argv[1];
	const auto path = (root / "live.so").string();
	auto& loader = BotEngineLoader::getInstance();
	const auto replace = [&](const std::string& variant) {
		fs::copy_file(root / (variant + ".so"), path, fs::copy_options::overwrite_existing);
	};
	assert(!loader.tryGetEngine());
	assert(!loader.load(path));
	assert(!loader.tryGetEngine());
	replace("good");
	assert(loader.prepareReload()); // recover without restarting after initial failure
	assert(loader.commitReload(loader.preparedTicket()));
	auto* original = loader.tryGetEngine();
	assert(original && original->countActiveBots() == 7);
	fs::remove(path);
	assert(!loader.reload());
	assert(loader.tryGetEngine() == original);
	std::cout << "PASS: absent replacement preserves active engine; initial recovery works\n";
	fs::create_directory(path); // copy_file must fail, without fallback to dlopen(source).
	assert(!loader.prepareReload());
	assert(loader.tryGetEngine() == original);
	fs::remove(path);
	std::cout << "PASS: snapshot copy failure preserves active engine\n";
	for (const auto* variant : {"invalid", "abi", "missingabi", "symbols", "factory", "data", "throwfactory", "throwdata"}) {
		replace(variant);
		assert(!loader.reload());
		assert(loader.tryGetEngine() == original && original->countActiveBots() == 7);
		std::cout << "PASS: rejected " << variant << " in phase=" << loader.phase() << '\n';
	}
	replace("good");
	assert(loader.prepareReload());
	const auto ticket = loader.preparedTicket();
	assert(!loader.prepareReload()); // a second request cannot replace the pending candidate
	assert(!loader.commitReload(ticket + 1));
	assert(loader.tryGetEngine() == original);
	loader.cancelReload(ticket + 1);
	assert(loader.preparedTicket() == ticket);
	loader.cancelReload(ticket);
	assert(!loader.commitReload(ticket));
	assert(loader.tryGetEngine() == original);
	std::cout << "PASS: stale tickets and cancellation preserve active engine\n";
	assert(loader.prepareReload());
	replace("invalid");
	assert(loader.commitReload(loader.preparedTicket())); // consumes snapshot, not live.so
	assert(loader.tryGetEngine() != original && loader.getEngine().countActiveBots() == 7);
	std::cout << "PASS: commit uses the exact prepared snapshot\n";
	replace("throwinit");
	assert(loader.prepareReload());
	assert(loader.commitReload(loader.preparedTicket()));
	assert(!loader.initialize());
	assert(!loader.isLoaded() && loader.phase() == "initialize");
	std::cout << "PASS: initialization exception leaves an explicit unavailable state\n";
	for (int iteration = 0; iteration < 50; ++iteration) {
		replace("good");
		assert(loader.reload());
		assert(loader.getEngine().countActiveBots() == 7);
	}
	loader.unload();
	assert(!loader.tryGetEngine());
	for (const auto& entry : fs::directory_iterator(root)) {
		assert(entry.path().string().find(".reload-") == std::string::npos);
	}
	std::ifstream maps("/proc/self/maps");
	std::string line;
	while (std::getline(maps, line)) assert(line.find(path + ".reload-") == std::string::npos);
	std::cout << "PASS: 50 reloads leave no snapshot files or mapped modules\n";
}
