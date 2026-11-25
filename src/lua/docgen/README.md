# Lua API Doc Generator (`src/lua/docgen`)

## Overview
Scans C++ Lua binding registrations across the repository and generates machine- and human-readable Lua API documentation in EmmyLua, Markdown, and JSON formats.

## Interface
- `LuaFunctionInfo`, `LuaClassInfo`, `LuaScanResult`, `TransparentStringHash`, `LuaStringSet`, `LuaStringMap` (`[lua_api_doc_generator.hpp:LuaFunctionInfo]`, `[lua_api_doc_generator.hpp:LuaClassInfo]`, `[lua_api_doc_generator.hpp:LuaScanResult]`): Data model representing discovered Lua global functions, classes, base classes, fields, overloads, parameters, and return types.
- `LuaBindingScanner` (`[lua_api_doc_generator.hpp:LuaBindingScanner]`, `[lua_api_doc_generator.cpp:LuaBindingScanner::scan]`): Walks C++ binding sources from `rootPath` and parses `luaL_Reg` tables and registration calls (`parseLuaReg`, `parseRegistrations`), inferring parameter lists and return types.
- `LuaApiDocGenerator` (`[lua_api_doc_generator.hpp:LuaApiDocGenerator]`, `[lua_api_doc_generator.cpp:LuaApiDocGenerator::generate]`): Resolves project root and output directory, builds the class/global model, and runs `exportEmmyLua()`, `exportMarkdown()`, and `exportJson()`.
- `CMakeLists.txt` (`[CMakeLists.txt:target_sources]`): Adds `lua_api_doc_generator.cpp` to `${CORE_TARGET_NAME}`.

## Invariants
- `LuaApiDocGenerator::generate` relies on deterministic sorted maps (`std::map<std::string, LuaClassInfo, std::less<>>`) for reproducible doc outputs (`[lua_api_doc_generator.hpp:LuaApiDocGenerator::classes]`).
- `LuaBindingScanner` separates explicit documentation annotations (`hasExplicitDocumentation`) from inferred signatures (`inferParameters`, `normalizeReturnType`, `inferReturnByBody`) (`[lua_api_doc_generator.hpp:LuaBindingScanner]`).

## Side Effects
- Reads C++ source files under the resolved project root and writes generated EmmyLua, Markdown, and JSON documentation artifacts into `docsDirectory` (`[lua_api_doc_generator.hpp:LuaApiDocGenerator]`).

## Verification
- See the [C++ build and test guide](../../../tests/README.md#running-tests).
