# map

## Overview
Package implementation for `src/map`, providing component logic and data interfaces for map.

## Interface
- `getOrCreateTileFromCache` (`[map.cpp:getOrCreateTileFromCache]`)
- `dist` (`[map.cpp:dist]`)
- `tryPos` (`[map.cpp:tryPos]`)
- `isSightClear` (`[map.cpp:isSightClear]`)
- `Creature` (`[map.hpp:Creature]`)
- `Player` (`[map.hpp:Player]`)
- `Game` (`[map.hpp:Game]`)
- `Tile` (`[map.hpp:Tile]`)
- `Map` (`[map.hpp:Map]`)
- `FindPathParams` (`[map.hpp:FindPathParams]`)
- Subdirectory [`./house/README.md`](./house/README.md) - Sub-package for house
- Subdirectory [`./utils/README.md`](./utils/README.md) - Sub-package for utils

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[map.cpp]`)
- Schedules timed tasks or dispatcher callbacks (`[map.cpp]`)
- Emits system diagnostic logs (`[mapcache.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
