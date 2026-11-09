# map

## Overview
Package implementation for `src/lua/functions/map`, providing component logic and data interfaces for map.

## Interface
- `HouseFunctions` (`[house_functions.hpp:HouseFunctions]`)
- `init` (`[house_functions.hpp:init]`)
- `luaHouseCreate` (`[house_functions.hpp:luaHouseCreate]`)
- `luaHouseGetId` (`[house_functions.hpp:luaHouseGetId]`)
- `luaHouseGetName` (`[house_functions.hpp:luaHouseGetName]`)
- `luaHouseGetTown` (`[house_functions.hpp:luaHouseGetTown]`)
- `luaHouseGetExitPosition` (`[house_functions.hpp:luaHouseGetExitPosition]`)
- `luaHouseGetRent` (`[house_functions.hpp:luaHouseGetRent]`)
- `MapFunctions` (`[map_functions.hpp:MapFunctions]`)
- `init` (`[map_functions.hpp:init]`)

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[position_functions.cpp]`)
- Emits system diagnostic logs (`[tile_functions.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
