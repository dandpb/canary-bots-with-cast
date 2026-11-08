# Game Reload Functions (`src/game/functions`)

## Overview
Provides the live hot-reload dispatcher (`GameReload`) that reloads server configuration, Lua scripts, XML definitions, chat channels, outfits, mounts, familiars, imbuements, vocations, groups, items, monsters, NPCs, and raids at runtime.

## Interface
- `Reload_t` (`[game_reload.hpp:Reload_t]`): Enumeration of reloadable server subsystems (`RELOAD_TYPE_NONE` through `RELOAD_TYPE_LAST`).
- `GameReload` / `g_gameReload` (`[game_reload.hpp:GameReload]`, `[game_reload.hpp:g_gameReload]`): DI-managed singleton providing `init(Reload_t)` and `getReloadNumber(Reload_t)`.

## Invariants
- `GameReload::reloadAll` skips `Reload_t::RELOAD_TYPE_ALL` while iterating `magic_enum::enum_values<Reload_t>()` to prevent infinite recursion (`[game_reload.cpp:GameReload::reloadAll]`).
- `GameReload::reloadScripts` clears all registered Lua scripts (`g_scripts().clearAllScripts()`) and dynamic zones (`Zone::clearZones()`) and reloads core libraries and datapack scripts before reloading monsters, NPCs, and items (`[game_reload.cpp:GameReload::reloadScripts]`).

## Side Effects
- Clears and reloads global runtime registries across `g_chat()`, `g_configManager()`, `g_events()`, `g_modules()`, `g_game().outfits`, `g_game().mounts`, `g_game().familiars`, `g_imbuements()`, `g_vocations()`, `g_luaEnvironment()`, `g_scripts()`, `Zone`, `Item::items`, `g_monsters()`, `g_npcs()`, and `g_game().raids` (`[game_reload.cpp:GameReload::init]`).
- Reads XML, Lua, and configuration files from disk and logs reload outcomes via `g_logger()` (`[game_reload.cpp:logReloadStatus]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
