# Documentation & Refactoring Python Scripts (`docs/python-scripts`)

## Overview
Provides standalone Python maintenance utilities used for bulk refactoring of Lua monster callbacks and C++ header/source include and `LuaScriptInterface` patterns across the repository.

## Interface
- `[convert_monsters_callbacks.py:get_root_path]`, `[convert_monsters_callbacks.py:process_lua_code]`, `[convert_monsters_callbacks.py:process_lua_file]`, `[convert_monsters_callbacks.py:process_all_lua_files]`, `[convert_monsters_callbacks.py:main]` — Recursively scans `.lua` files from the repository root and strips `mType.onAppear` and empty `mType.<callback>` functions.
- `[modify_lua_script_interfaces.py:remove_constructor_and_destructor]`, `[modify_lua_script_interfaces.py:remove_include_luascript]`, `[modify_lua_script_interfaces.py:remove_final_luascriptinterface]`, `[modify_lua_script_interfaces.py:move_init_function_to_cpp]`, `[modify_lua_script_interfaces.py:add_include_to_cpp]`, `[modify_lua_script_interfaces.py:process_files]`, `[modify_lua_script_interfaces.py:convert_to_static]`, `[modify_lua_script_interfaces.py:main]` — Refactors `.hpp`/`.cpp` files (default `../../src/lua/functions/`) to remove `LuaScriptInterface` inheritance and prefix helper calls in `functions_to_convert` with `Lua::`.
- `[normalize_cpp_own_includes.py.py:normalize_include_line]`, `[normalize_cpp_own_includes.py.py:correct_include_path]`, `[normalize_cpp_own_includes.py.py:modify_includes]` — Normalizes each `.cpp` file's own `.hpp` `#include` path and moves it to the first `#include` position.
- `[remove_player_includes.py:remove_includes]`, `[remove_player_includes.py:update_method_calls]`, `[remove_player_includes.py:process_files]`, `[remove_player_includes.py:main]` — Removes legacy player sub-header includes (`includes_to_remove`) and rewrites pointer calls (`wheel()->`, `vip()->`, etc.) to value calls (`wheel().`) in `.cpp`/`.hpp` files.

## Invariants
- `[modify_lua_script_interfaces.py:files_to_exclude]` skips `lua_functions_loader.cpp` and `lua_functions_loader.hpp`, and `[modify_lua_script_interfaces.py:convert_to_static]` preserves `g_configManager().` method calls without prefixing `Lua::`.
- `[normalize_cpp_own_includes.py.py:directory_path]` defaults to placeholder `"path/to/src"` and must be pointed at a valid source tree when invoked.

## Side Effects
- All four scripts (`convert_monsters_callbacks.py`, `modify_lua_script_interfaces.py`, `normalize_cpp_own_includes.py.py`, `remove_player_includes.py`) overwrite matching `.lua`, `.cpp`, and `.hpp` source files in-place when regex transformations produce changes.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
