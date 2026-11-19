# CMake Build Modules (`cmake/modules`)

## Overview
Provides reusable CMake configuration modules defining compiler flags, target architecture settings, logging helpers, and third-party dependency discovery for the `canary` executable and `libbot_engine.so`.

## Interface
- `[CanaryLib.cmake]` — Configures shared compilation flags, warnings, IPO/LTO, and Release/RelWithDebInfo optimization (`-O3 -march=${CANARY_TARGET_ARCH}` on GCC/Clang) for both the core server library and `libbot_engine`.
- `[BaseConfig.cmake]` — Base CMake build-type, C++ standard, and platform defaults.
- `[FindLuaJIT.cmake]` / `[FindMySQL.cmake]` / `[FindPugiXML.cmake]` — CMake finder modules for LuaJIT, MySQL/MariaDB client, and PugiXML.
- `[LoggingHelper.cmake]` / `[MessageColors.cmake]` — Formatted CMake diagnostic output helpers.

## Invariants
- `[CanaryLib.cmake]` applies the exact same `-march=${CANARY_TARGET_ARCH}` target flag to both the core server target and `libbot_engine` so Release builds share a consistent ABI/ISA baseline (default `"native"`, overridden to `"armv8-a"` in portable ARM64 release builds).

## Side Effects
- Mutates CMake target compile/link options and cache variables during `cmake` configuration.

## Verification
- Run: `cmake --preset linux-release --dry-run || cmake --list-presets`
