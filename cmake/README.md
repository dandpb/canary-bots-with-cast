# CMake Build Support (`cmake`)

## Overview
Groups root CMake build-time helper scripts (bot engine ABI tagging, symbol hygiene checks, shared build cache identity, Git metadata generation), Windows vcpkg triplets, and CMake configuration modules.

## Interface
- `BotEngineAbiTag.cmake`: Build-time `-P` script hashing `BOT_ABI_TOOLCHAIN` and sorted `BOT_ABI_HEADERS` (CR-stripped SHA-256) into `bot_engine_abi_tag.hpp`, rewriting only on hash changes (`[BotEngineAbiTag.cmake]`).
- `check_bot_engine_symbols.cmake`: Post-build verification script inspecting `libbot_engine.so` via `readelf --dyn-syms --wide` for disallowed `GNU_UNIQUE` or leaked symbols and deleting the artifact on failure (`[check_bot_engine_symbols.cmake]`).
- `SharedBuildCache.cmake`: Defines shared build cache schema (`CANARY_SHARED_CACHE_SCHEMA = "v5"`) and dependency contract (`CANARY_SHARED_CACHE_DEPENDENCY_CONTRACT = "vcpkg-inputs-v2"`) (`[SharedBuildCache.cmake]`).
- `SourceMetadata.cmake` / `WriteSourceMetadata.cmake` / `git_watcher.cmake` / `gitmetadata.h.in`: Build-time `canary_source_metadata` target refreshing `gitmetadata.h` with live 40-char Git SHA and dirty state (`[SourceMetadata.cmake:canary_target_source_metadata]`, `[WriteSourceMetadata.cmake]`).
- `canary.rc` / `canary.ico`: Windows executable version/icon resource files.
- `triplets/`: Custom vcpkg triplets (`x64-windows-static-release.cmake`, `x64-windows-test-debug.cmake`, `x64-windows-test-release.cmake`).
- Subdirectory [`./modules/README.md`](./modules/README.md) — Core CMake configuration modules (`CanaryLib.cmake`, `BaseConfig.cmake`, dependency finders, and logging helpers).

## Invariants
- `BotEngineAbiTag.cmake` strips `\r` before hashing headers so Windows CRLF and Linux LF checkouts produce identical ABI tags (`[BotEngineAbiTag.cmake]`).
- `check_bot_engine_symbols.cmake` deletes the built `libbot_engine.so` if symbol hygiene checks fail so Ninja cannot retain an invalid shippable binary (`[check_bot_engine_symbols.cmake]`).
- `WriteSourceMetadata.cmake` never retains a cached commit identity after a Git lookup failure (`[WriteSourceMetadata.cmake]`).

## Side Effects
- Generates/updates `bot_engine_abi_tag.hpp` and `source-metadata/gitmetadata.h` inside the CMake binary directory during builds, and removes invalid `libbot_engine.so` artifacts on post-build check failure (`[BotEngineAbiTag.cmake]`, `[SourceMetadata.cmake]`, `[check_bot_engine_symbols.cmake]`).

## Verification
- Run `cmake --list-presets=all` from the repository root, or see the [C++ build and test guide](../tests/README.md#running-tests).
