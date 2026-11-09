# utils

## Overview
Package implementation for `src/map/utils`, providing component logic and data interfaces for utils.

## Interface
- `Position` (`[astarnodes.hpp:Position]`)
- `Creature` (`[astarnodes.hpp:Creature]`)
- `Tile` (`[astarnodes.hpp:Tile]`)
- `AStarNode` (`[astarnodes.hpp:AStarNode]`)
- `AStarNodes` (`[astarnodes.hpp:AStarNodes]`)
- `createOpenNode` (`[astarnodes.hpp:createOpenNode]`)
- `getBestNode` (`[astarnodes.hpp:getBestNode]`)
- `Creature` (`[mapsector.hpp:Creature]`)
- `Tile` (`[mapsector.hpp:Tile]`)
- `BasicTile` (`[mapsector.hpp:BasicTile]`)

## Invariants
- Validation assertion: `assert(index < MAX_NODES)` (`[astarnodes.cpp]`)
- Validation assertion: `assert(iter != creature_list.end()` (`[mapsector.cpp]`)
- Validation assertion: `assert(iter != player_list.end()` (`[mapsector.cpp]`)
- Validation assertion: `assert(iter != monster_list.end()` (`[mapsector.cpp]`)
- Validation assertion: `assert(iter != npc_list.end()` (`[mapsector.cpp]`)

## Side Effects
- Emits system diagnostic logs (`[mapsector.cpp]`)
- Emits system diagnostic logs (`[mapsector.hpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
