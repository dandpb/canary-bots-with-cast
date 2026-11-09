# Core Game Lua Functions

## Overview
Provides the C++-to-Lua bindings for core game state, global script functions, configuration keys, banking operations, modal dialog windows, spatial zones, and global enumeration constants. This package exposes the `Game`, `Bank`, `configManager`, `configKeys`, `ModalWindow`, and `Zone` tables/classes, along with top-level Lua helper functions and game enums, into the active `lua_State*`.

## Interface
- `CoreGameFunctions` (`[core_game_functions.hpp:CoreGameFunctions]`) — Aggregator `LuaScriptInterface` subclass that initializes `ConfigFunctions`, `GameFunctions`, `BankFunctions`, `GlobalFunctions`, `LuaEnums`, and `ModalWindowFunctions` via `CoreGameFunctions::init(lua_State* L)` (`[core_game_functions.hpp:CoreGameFunctions::init]`).
- `BankFunctions` (`[bank_functions.hpp:BankFunctions]`) — Registers the Lua `Bank` table (`credit`, `debit`, `balance`, `hasBalance`, `transfer`, `transferToGuild`, `withdraw`, `deposit`) via `BankFunctions::init(lua_State* L)` (`[bank_functions.cpp:BankFunctions::init]`).
- `ConfigFunctions` (`[config_functions.hpp:ConfigFunctions]`) — Registers the Lua `configManager` table (`getString`, `getNumber`, `getBoolean`, `getFloat`) and the `configKeys` enum table (including `BOT_POPULATION_REFERENCE_BOTS`) via `ConfigFunctions::init(lua_State* L)` (`[config_functions.cpp:ConfigFunctions::init]`).
- `GameFunctions` (`[game_functions.hpp:GameFunctions]`) — Registers the Lua `Game` table for world queries, entity/map creation, bestiary/bosstiary/achievements, and bot lifecycle/hibernation/market hooks via `GameFunctions::init(lua_State* L)` (`[game_functions.cpp:GameFunctions::init]`).
- `GlobalFunctions` (`[global_functions.hpp:GlobalFunctions]`) — Registers global Lua C functions (`addEvent`, `stopEvent`, `cleanMap`, `saveServer`, `createCombatArea`, `doPlayerAddItem`, `doAddContainerItem`, area/target combat helpers, `isType`, `rawgetmetatable`, `createTable`, `systemTime`, `reportError`, etc.) and globals (`INDEX_WHEREEVER`, `VIRTUAL_PARENT`) via `GlobalFunctions::init(lua_State* L)` (`[global_functions.cpp:GlobalFunctions::init]`).
- `LuaEnums` (`[lua_enums.hpp:LuaEnums]`) — Registers all C++ game, combat, condition, item, creature, webhook, sound, wheel, virtue, and monk spell enumerations into the global Lua namespace via `LuaEnums::init(lua_State* L)` (`[lua_enums.hpp:LuaEnums::init]`).
- `ModalWindowFunctions` (`[modal_window_functions.hpp:ModalWindowFunctions]`) — Registers the `ModalWindow` shared Lua class and its dialog builder/sender methods via `ModalWindowFunctions::init(lua_State* L)` (`[modal_window_functions.cpp:ModalWindowFunctions::init]`).
- `ZoneFunctions` (`[zone_functions.hpp:ZoneFunctions]`) — Registers the `Zone` shared Lua class (`addArea`, `subtractArea`, `getPositions`, `getCreatures`, `getPlayers`, `getMonsters`, `getNpcs`, `getItems`, `removePlayers`, `removeMonsters`, `removeNpcs`, `refresh`, `setMonsterVariant`, `getByPosition`, `getByName`, `getAll`) via `ZoneFunctions::init(lua_State* L)` (`[zone_functions.cpp:ZoneFunctions::init]`).

## Invariants
- `BankFunctions` methods require a valid `Player` or `Guild` target resolvable to a `Bank` instance via `BankFunctions::getBank` (`[bank_functions.cpp:BankFunctions::getBank]`), reporting a Lua error if `nullptr`.
- `ConfigFunctions` getters require a valid `ConfigKey_t` enum key on the Lua stack (`[config_functions.cpp:ConfigFunctions::luaConfigManagerGetString]`, `[config_functions.cpp:ConfigFunctions::luaConfigManagerGetFloat]`).
- `GameFunctions::luaGameCreateMonsterType` errors if a `MonsterType` with the resolved name or variant name is already registered in `g_monsters()` (`[game_functions.cpp:GameFunctions::luaGameCreateMonsterType]`).
- `ModalWindowFunctions::luaModalWindowSendToPlayer` only sends the modal window if `!player->hasModalWindowOpen(window->id)` (`[modal_window_functions.cpp:ModalWindowFunctions::luaModalWindowSendToPlayer]`).
- Note: `ZoneFunctions::init` is invoked directly from `Lua::load` (`[lua_functions_loader.cpp:Lua::load]`) rather than inside `CoreGameFunctions::init` (`[core_game_functions.hpp:CoreGameFunctions::init]`).

## Side Effects
- Mutates the Lua state global tables and metatables (`Bank`, `configManager`, `configKeys`, `Game`, `ModalWindow`, `Zone`, and global functions/enums) (`[core_game_functions.hpp:CoreGameFunctions::init]`, `[zone_functions.cpp:ZoneFunctions::init]`).
- Mutates player and guild bank balances and in-game currency (`g_game().removeMoney`, `Bank::credit`, `Bank::debit`, `Bank::transferTo`, `Bank::withdraw`) (`[bank_functions.cpp:BankFunctions::luaBankDeposit]`, `[bank_functions.cpp:BankFunctions::luaBankTransfer]`).
- Spawns creatures/items/tiles, loads map chunks, triggers raids/reloads/saves, and controls bot engine states (`g_game()`, `g_monsters()`, `g_saveManager()`, `Zone::addZone`) (`[game_functions.cpp:GameFunctions::init]`, `[global_functions.cpp:GlobalFunctions::init]`, `[zone_functions.cpp:ZoneFunctions::luaZoneCreate]`).
- Dispatches network packets to players such as modal windows and channel messages (`player->sendModalWindow`) (`[modal_window_functions.cpp:ModalWindowFunctions::luaModalWindowSendToPlayer]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
