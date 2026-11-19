# CMake Build Modules (`cmake/modules`)

## Overview
Provides reusable CMake configuration modules defining compiler flags, target architecture settings, logging helpers, and third-party dependency discovery for the `canary` executable and `libbot_engine.so`.

## Interface
- `[CanaryLib.cmake]` — Configures shared compilation flags, warnings, IPO/LTO, and Release/RelWithDebInfo optimization (`-O3 -march=${CANARY_TARGET_ARCH}` on GCC/Clang) for the core server library.
- `[BaseConfig.cmake]` — Base CMake build-type, C++ standard, and platform defaults.
- `[FindLuaJIT.cmake]` / `[FindMySQL.cmake]` / `[FindPugiXML.cmake]` — CMake finder modules for LuaJIT, MySQL/MariaDB client, and PugiXML.
- `[LoggingHelper.cmake]` / `[MessageColors.cmake]` — Formatted CMake diagnostic output helpers.

## Invariants
- Release and RelWithDebInfo share the same architecture setting across the core library and `libbot_engine`. The plugin applies it in [the creatures target](../../src/creatures/CMakeLists.txt). The default is `"native"`, with `"armv8-a"` used in the portable ARM64 release build.

## Side Effects
- Mutates CMake target compile/link options and cache variables during `cmake` configuration.

## Verification
- From the repository root, run `cmake --list-presets=all` to list and validate the preset definitions. See the [test guide](../../tests/README.md#running-tests) to configure and build a preset.
