# Player Storages Registry

## Overview
Loads and validates named player storage key definitions and reserved ranges from `XML/storages.xml` (`Storages`), allowing scripts and engine subsystems to reference storage keys by symbolic name.

## Interface
- `Storages` (`[storages.hpp:Storages]`, `[storages.cpp:Storages]`): Singleton (`getInstance()`) providing `loadFromXML()` (`[storages.cpp:Storages::loadFromXML]`) and `getStorageMap()` (`[storages.hpp:Storages::getStorageMap]`).

## Invariants
- The loader adds the containing range's start to each storage key. It skips the entry if the result exceeds the declared end, and warns about uppercase names (`[storages.cpp:Storages::loadFromXML]`).

## Side Effects
- Reads `XML/storages.xml` under the configured core directory and populates `m_storageMap` (`[storages.cpp:Storages::loadFromXML]`).

## Verification
- See the [C++ build and test guide](../../../../tests/README.md#running-tests).
