# items

## Overview
Package implementation for `src/lua/functions/items`, providing component logic and data interfaces for items.

## Interface
- `ContainerFunctions` (`[container_functions.hpp:ContainerFunctions]`)
- `init` (`[container_functions.hpp:init]`)
- `luaContainerCreate` (`[container_functions.hpp:luaContainerCreate]`)
- `luaContainerGetSize` (`[container_functions.hpp:luaContainerGetSize]`)
- `luaContainerGetMaxCapacity` (`[container_functions.hpp:luaContainerGetMaxCapacity]`)
- `luaContainerGetCapacity` (`[container_functions.hpp:luaContainerGetCapacity]`)
- `luaContainerGetEmptySlots` (`[container_functions.hpp:luaContainerGetEmptySlots]`)
- `luaContainerGetContentDescription` (`[container_functions.hpp:luaContainerGetContentDescription]`)
- `ImbuementFunctions` (`[imbuement_functions.hpp:ImbuementFunctions]`)
- `init` (`[imbuement_functions.hpp:init]`)

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[item_functions.cpp]`)
- Emits system diagnostic logs (`[weapon_functions.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
