# Player Storages Registry

## Overview
Loads and validates named player storage key definitions and reserved ranges from `XML/storages.xml` (`Storages`), allowing scripts and engine subsystems to reference storage keys by symbolic name.

## Interface
- `Storages` (`[storages.hpp:Storages]`, `[storages.cpp:Storages]`): Singleton (`getInstance()`) providing `loadFromXml()` (`[storages.cpp:Storages::loadFromXml]`) and `getStorageMap()` (`[storages.hpp:Storages::getStorageMap]`).

## Invariants
- Storage keys within the engine's reserved range (`PSTRG_RESERVED_RANGE_START` to `PSTRG_RESERVED_RANGE_SIZE`, `10000000`–`20000000`) cannot be registered in `XML/storages.xml` and are skipped with a warning (`[storages.cpp:Storages::loadFromXml]`).

## Side Effects
- Reads `XML/storages.xml` from disk and populates `m_storageMap` (`[storages.cpp:Storages::loadFromXml]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
