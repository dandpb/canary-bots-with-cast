# Game Engine Core (`src/game`)

## Overview
Coordinates the authoritative world simulation (`Game`), managing the lifecycle of the server (`GameState_t`), map loading (`Map`), creature/player/monster/NPC placement and movement, combat damage resolution, item manipulation, player protocol actions, cyclopedia/highscore/house-auction systems, and bot market/engine integration.

## Interface
- `Game` / `g_game` (`[game.hpp:Game]`, `[game.hpp:g_game]`): Central world controller singleton managing game state (`start`, `setGameState`, `getGameState`, `shutdown`, `dieSafely`), entity registries (`getCreatureByID`, `getPlayerByID`, `getPlayerByGUID`, `placeCreature`, `removeCreature`, `addPlayer`, `removePlayer`), movement & items (`internalMoveCreature`, `internalMoveItem`, `internalAddItem`, `internalRemoveItem`, `internalTeleport`, `transformItem`), combat (`combatBlockHit`, `combatChangeHealth`, `combatChangeMana`), player actions (`playerMove*`, `playerUse*`, `playerSay`, `playerCreateMarketOffer`, `playerAcceptMarketOffer`, `playerCancelMarketOffer`), and bot integration (`restartBotTickLoop`, `botCreateMarketOffer`, `botAcceptMarketOffer`, `botCancelMarketOffer`).
- `StackPosType_t`, `WorldType_t`, `GameState_t`, `QuickLootFilter_t`, `Faction_t`, `LightState_t`, `CyclopediaCharacterInfoType_t`, `CyclopediaCharacterInfo_RecentKillStatus_t`, `HighscoreCategories_t`, `HighscoreType_t`, `Webhook_Colors_t` (`[game_definitions.hpp:GameState_t]`, `[game_definitions.hpp:WorldType_t]`, `[game_definitions.hpp:HighscoreCategories_t]`): Core game enumerations.
- `QueryHighscoreCacheEntry`, `HighscoreCacheEntry` (`[game.hpp:QueryHighscoreCacheEntry]`, `[game.hpp:HighscoreCacheEntry]`): Highscore query and result cache structures.
- Child Subsystems:
  - [bank](./bank/README.md): Player and guild bank balance and transfer abstractions (`Bank`, `Bankable`).
  - [functions](./functions/README.md): Runtime hot-reload coordinator (`GameReload`).
  - [modal_window](./modal_window/README.md): Client modal dialog data structure (`ModalWindow`).
  - [movement](./movement/README.md): 3D coordinates (`Position`), directions (`Direction`), and `Teleport` items.
  - [scheduling](./scheduling/README.md): Asynchronous event loop (`Dispatcher`, `Task`), calendar rates (`EventsScheduler`), and persistence (`SaveManager`, `SerialSaveQueue`).
  - [zones](./zones/README.md): Spatial map zones (`Zone`, `Area`) and entity caches.

## Invariants
- Once `Game::setGameState(GAME_STATE_SHUTDOWN)` is entered, `gameState` cannot transition to any other state (`[game.cpp:Game::setGameState]`), and `Game::shutdown()` halts `g_dispatcher()` before clearing map spawns so scheduled callbacks cannot dereference destroyed spawn objects (`[dispatcher.hpp:Dispatcher::shutdown]`).
- `Game::restartBotTickLoop` cancels any previously active `botTickEventId` via `g_dispatcher().stopEvent` before scheduling a new 100ms `BotEngine::tick` cycle event, ensuring at most one bot tick loop runs at a time (`[game.cpp:Game::restartBotTickLoop]`).
- `Game::botCreateMarketOffer`, `Game::botAcceptMarketOffer`, and `Game::botCancelMarketOffer` validate marketable items (`it.id != 0 && it.wareId != 0`), clamp item tiers to `FORGE_MAX_ITEM_TIER` (or `0` if `upgradeClassification == 0`), forbid self-accept (`offer.playerId == bot->getGUID()`), and skip synchronous `savePlayer` calls on bot accounts (`[game_bot_market.cpp:Game::botCreateMarketOffer]`, `[game_bot_market.cpp:Game::botAcceptMarketOffer]`, `[game_bot_market.cpp:Game::botCancelMarketOffer]`).
- `Game::loadCustomMaps` loads at most 50 custom `.otbm` maps, skips filenames prefixed with `#` or matching the main `MAP_NAME`, and loads house info only after all maps finish loading (`[game.cpp:Game::loadCustomMaps]`).

## Side Effects
- Registers network protocols (`ProtocolGame`, `ProtocolLogin`, `ProtocolStatus`) on `ServiceManager`, dynamically loads `./libbot_engine.so` via `BotEngineLoader::getInstance()`, and schedules recurring world maintenance tasks on `g_dispatcher()` (`createFiendishMonsters`, `createInfluencedMonsters`, `updateForgeableMonsters`, `checkLight`, `checkCreatures`, `collectGarbage`, `loadItemsPrice`, `updatePlayersOnline`, `BotEngine::tick`) (`[game.cpp:Game::start]`, `[game.cpp:Game::restartBotTickLoop]`).
- Mutates world map tiles, creature positions, health/mana/conditions, player inventories, containers, houses, and market offers, and broadcasts network packets to spectators (`[game.cpp:Game::setGameState]`, `[game_bot_market.cpp:Game::botAcceptMarketOffer]`).
- Executes synchronous and asynchronous database queries via `Database`, `IOMarket`, `IOLoginData`, `IOWheel`, `g_botDatabaseTasks()`, and `g_saveManager()` (`[game.cpp:Game::loadBoostedCreature]`, `[game.cpp:Game::loadItemsPrice]`, `[game_bot_market.cpp:Game::botCreateMarketOffer]`, `[game_bot_market.cpp:Game::botAcceptMarketOffer]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
