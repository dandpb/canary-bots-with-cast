# config

## Overview
Manages server configuration loading, reloading, and typed lookup from `config.lua`, including core server settings, OTClient feature flags (`OTCRFeatures`), and X-macro tables defining bot navigation, activity, market, party trail, ambient roam, corpse loot, lure/kite, and shrine configuration keys.

## Interface
- `ConfigManager` & `g_configManager` (`[configmanager.hpp:ConfigManager]`, `[configmanager.hpp:g_configManager]`): DI-backed singleton (`[configmanager.cpp:ConfigManager::getInstance]`) that loads/reloads `config.lua` (`[configmanager.hpp:ConfigManager::load]`, `[configmanager.hpp:ConfigManager::reload]`, `[configmanager.hpp:ConfigManager::setConfigFileLua]`, `[configmanager.hpp:ConfigManager::getConfigFileLua]`) and provides typed accessors (`[configmanager.hpp:ConfigManager::getString]`, `[configmanager.hpp:ConfigManager::getNumber]`, `[configmanager.hpp:ConfigManager::getBoolean]`, `[configmanager.hpp:ConfigManager::getFloat]`, `[configmanager.hpp:ConfigManager::getEnabledFeaturesOTC]`, `[configmanager.hpp:ConfigManager::getDisabledFeaturesOTC]`).
- `ConfigValue` & `OTCFeatures` (`[configmanager.hpp:ConfigValue]`, `[configmanager.hpp:OTCFeatures]`): Type aliases for stored variant config values (`std::variant<std::string, int32_t, bool, float>`) and OTClient feature byte vectors.
- `ConfigKey_t` (`[config_enums.hpp:ConfigKey_t]`): Enumeration of all configuration keys spanning core server parameters and bot engine tunables.
- Bot Config X-Macro Tables (`[bot_config_keys.hpp:BOT_NAV_REALISM_CONFIG_KEYS]`, `[bot_config_keys.hpp:BOT_ACTIVITY_CONFIG_KEYS]`, `[bot_config_keys.hpp:BOT_MARKET_CONFIG_KEYS]`, `[bot_config_keys.hpp:BOT_PARTY_TRAIL_CONFIG_KEYS]`, `[bot_config_keys.hpp:BOT_AMBIENT_ROAM_CONFIG_KEYS]`, `[bot_config_keys.hpp:BOT_CORPSE_LOOT_CONFIG_KEYS]`, `[bot_config_keys.hpp:BOT_ACTIVITY_PCT_CONFIG_KEYS]`, `[bot_config_keys.hpp:BOT_LURE_KITE_CONFIG_KEYS]`, `[bot_config_keys.hpp:BOT_SHRINE_CONFIG_KEYS]`): Single-source-of-truth macro tables generating `ConfigKey_t` enumerators and `ConfigManager::load` calls.

## Invariants
- `BOT_*` X-macro tables and trailing enum keys in `ConfigKey_t` are strictly append-only (`BOT_SHRINE_CONFIG_KEYS` expanded last among bot tables, followed by post-table keys like `FORCE_LOGOUT_ON_CONNECTION_LOSS` and `BOT_POPULATION_REFERENCE_BOTS`) so that hot-reloaded `libbot_engine.so` ordinal lookups never shift (`[config_enums.hpp:ConfigKey_t]`, `[bot_config_keys.hpp:BOT_SHRINE_CONFIG_KEYS]`).
- Startup-only configuration keys (guarded by `if (!loaded)` in `ConfigManager::load`, such as `BIND_ONLY_GLOBAL_ADDRESS`, `OLD_PROTOCOL`, `OPTIMIZE_DATABASE`, `TOGGLE_MAP_CUSTOM`) are parsed only on initial load and not overwritten until reset (`[configmanager.cpp:ConfigManager::load]`).
- Activity percentage tables (`TABLE A` in `BOT_ACTIVITY_PCT_CONFIG_KEYS`, `TABLE B` across `BOT_ACTIVITY_PCT_CONFIG_KEYS` and `BOT_SHRINE_CONFIG_KEYS`, and `TABLE C` across `BOT_ACTIVITY_PCT_CONFIG_KEYS` and `BOT_SHRINE_CONFIG_KEYS`) are designed to sum to 100 (`[bot_config_keys.hpp:BOT_ACTIVITY_PCT_CONFIG_KEYS]`, `[bot_config_keys.hpp:BOT_SHRINE_CONFIG_KEYS]`).

## Side Effects
- Allocates a Lua state (`luaL_newstate`), opens standard libraries, and executes the Lua configuration file from disk via `luaL_dofile` (`[configmanager.cpp:ConfigManager::load]`).
- Mutates internal configuration maps (`configs`) and lazy per-type lookup caches (`m_configString`, `m_configInteger`, `m_configBoolean`, `m_configFloat`) even on `const` getter calls (`[configmanager.hpp:ConfigManager]`, `[configmanager.cpp:ConfigManager::getString]`, `[configmanager.cpp:ConfigManager::getNumber]`, `[configmanager.cpp:ConfigManager::getBoolean]`, `[configmanager.cpp:ConfigManager::getFloat]`, `[configmanager.cpp:ConfigManager::reload]`).
- Logs warnings and errors via `g_logger()` on missing config identifiers, file load errors, or type/key mismatches (`[configmanager.cpp:ConfigManager::load]`, `[configmanager.cpp:ConfigManager::missingConfigWarning]`, `[configmanager.cpp:ConfigManager::getString]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
