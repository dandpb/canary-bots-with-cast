# Bot Engine Subsystem

## Overview
Implements the autonomous player bot subsystem (`libbot_engine.so`) and its hot-reloadable loader (`BotEngineLoader`). Manages bot lifecycle, hibernation and virtual simulation, 2D A* and multi-floor portal navigation (`botnav`), solo and party hunting, combat/spell/rune evaluation, PvP/gang-PK tactics, ambient city liveness (POIs, houses, shrines, fishing, chat), authored CSV data loading/editing, and external brain telemetry/intent IPC (`botbrain`).

## Interface
- `IBotEngine`, `BotState`, `BotReloadSnapshot`, `BotReloadEntry`, `BotPlayerSnapshot`, `HuntScript`, `Waypoint`, `CityRouteGraph`, `BotPOI`, `BotAIState`, `POIType`, `HuntPhase`, `FloorChangeState` (`[bot_engine_interface.hpp:IBotEngine]`, `[bot_engine_interface.hpp:BotState]`, `[bot_engine_interface.hpp:HuntScript]`, `[bot_engine_interface.hpp:Waypoint]`): Public ABI boundary between the main server binary and `libbot_engine.so`.
- `BotEngineLoader`, `getBotEngineInstance`, `getBotEngineIfLoaded`, `g_botEngine` (`[bot_engine_loader.hpp:BotEngineLoader]`, `[bot_engine_loader.cpp:BotEngineLoader]`, `[bot_engine.hpp:getBotEngineInstance]`, `[bot_engine.hpp:g_botEngine]`): Singleton dynamic library loader supporting two-phase `prepareReload()` / `commitReload()` / `initialize()` with private `.so` snapshots and state handoff.
- `botEngineAbiTag`, `prepareBotEngine`, `createBotEngine`, `destroyBotEngine` (`[bot_engine_abi.hpp:BotEngineAbiFunc]`, `[bot_engine.cpp:botEngineAbiTag]`, `[bot_engine.cpp:createBotEngine]`): Exported `extern "C"` factory and ABI verification hooks in `libbot_engine.so`.
- `BotEngine` (`[bot_engine_impl.hpp:BotEngine]`, `[bot_engine.cpp:BotEngine]`): Concrete implementation of `IBotEngine` spanning lifecycle (`bot_engine.cpp`), dispatcher tick and virtual simulation (`bot_tick.cpp`), navigation and floor transitions (`bot_waypoint.cpp`, `bot_zgraph.cpp`), hunting/luring/kiting/corpse looting (`bot_hunt.cpp`), party hunts and trail following (`bot_party.cpp`), combat/PvP/gang-PK (`bot_combat.cpp`), POIs/houses/shrines/fishing (`bot_poi.cpp`, `bot_house.cpp`), ambient liveness/chat (`bot_liveness.cpp`, `bot_chat.cpp`), CSV data/editing (`bot_data.cpp`, `bot_csvedit.cpp`), debug/commands (`bot_debug.cpp`), and brain IPC (`bot_brain.cpp`).
- `botnav::findPath`, `botnav::PathNodePool`, `botnav::PathParams` (`[bot_pathcore.hpp:botnav::findPath]`, `[bot_pathcore.hpp:botnav::PathNodePool]`): Dependency-free 2D A* pathfinding kernel shared between the live server and `tools/botnavsim`.
- `botnav::ZPortalGraph`, `botnav::ZPortal`, `botnav::planZRoute`, `botnav::zSnapLandingT` (`[bot_zcore.hpp:botnav::ZPortalGraph]`, `[bot_zcore.hpp:botnav::planZRoute]`): Dependency-free multi-floor portal graph and Dijkstra cross-floor route planner.
- `botnav::NavDump` (`[bot_navdump.hpp:botnav::NavDump]`): Binary map-dump serialization format (`BNDV` v1/v2) for offline pathfinding simulation.
- `botbrain::Channel`, `botbrain::TelemetryOutbox`, `botbrain::Session`, `botbrain::Runtime`, `botbrain::validate` (`[bot_brain_channel.hpp:botbrain::Channel]`, `[bot_brain_channel.hpp:botbrain::Runtime]`, `[bot_brain_protocol.hpp:botbrain::validate]`): Non-blocking AF_UNIX datagram channel, bounded telemetry outbox, and intent validation protocol for external pilot brains.
- `botsupplies::PotionDef`, `botsupplies::kPotions`, `botsupplies::vocBit` (`[bot_potions.hpp:botsupplies::PotionDef]`, `[bot_potions.hpp:botsupplies::kPotions]`): Vocation and level-gated potion definitions.

## Invariants
- `botEngineAbiTag()` must match `BOT_ENGINE_ABI_TAG` before `BotEngineLoader::prepare` invokes factory or vtable symbols (`[bot_engine_abi.hpp:BOT_ENGINE_ABI_TAG]`, `[bot_engine_loader.cpp:BotEngineLoader::prepare]`).
- All `BotEngine` tick, wake, hibernate, and chat callbacks execute on the single serial dispatcher thread (`[bot_engine_impl.hpp:botThreadCpuUs]`).
- When authored CSV loading fails, `dataPoisoned_` is set and `activateBot` refuses all bot activations rather than running on partial or empty data (`[bot_engine.cpp:BotEngine::activateBot]`).
- Hibernated bots preserve their `Player` instance in `hibernationPool_` while unlinked from `g_game().getPlayers()` and the world map; bots with active cast viewers (`getCastViewerCount() > 0`), human-led party members, or dying state (`dyingBots_`) must not hibernate (`[bot_engine.cpp:BotEngine::hibernateBot]`).
- Reload snapshots (`BotReloadSnapshot`) transfer only value types and executable-owned `std::shared_ptr<Player>` handles across `dlclose()`, cancelling pending dispatcher events (`cancelPendingDispatcherEvents`) before unloading the old module (`[bot_engine.cpp:BotEngine::quiesceForReload]`, `[bot_engine_loader.cpp:BotEngineLoader::commitReload]`).

## Side Effects
- Copies `libbot_engine.so` into a private `mkdtemp` directory and loads/unloads it via `dlopen` / `dlclose` (`[bot_engine_loader.cpp:BotEngineLoader::prepare]`, `[bot_engine_loader.cpp:BotEngineLoader::Module::~Module]`).
- Mutates world state by placing, moving, teleporting, equipping, and removing bot `Player` instances in `Game` and `Map`, casting spells, using items, and dispatching chat messages (`[bot_engine.cpp:BotEngine::materializePlayerFromDb]`, `[bot_engine.cpp:BotEngine::activateBot]`, `[bot_engine.cpp:BotEngine::deactivateBot]`).
- Executes synchronous and asynchronous SQL queries via `Database` and `g_botDatabaseTasks()` (`bot_active_players`, `cast_broadcasters`, `bot_state_persistence`) and checkpoints player state via `g_saveManager()` (`[bot_engine.cpp:BotEngine::registerBot]`, `[bot_engine.cpp:BotEngine::checkpointBotPersistentState]`, `[bot_engine.cpp:BotEngine::saveAllStates]`).
- Reads and writes authored CSV/JSON/binary cache files under `data/bot/` and `data/bot_chat/`, and binds non-blocking Unix domain sockets (`server.sock`, `server.lock`) when `botbrain::Runtime` is enabled (`[bot_brain_channel.hpp:botbrain::Channel]`, `[bot_engine_impl.hpp:BotEngine]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
