# house

## Overview
Package implementation for `src/map/house`, providing component logic and data interfaces for house.

## Interface
- `iss` (`[house.cpp:iss]`)
- `getGuildByName` (`[house.cpp:getGuildByName]`)
- `House` (`[house.hpp:House]`)
- `BedItem` (`[house.hpp:BedItem]`)
- `Player` (`[house.hpp:Player]`)
- `AccessList` (`[house.hpp:AccessList]`)
- `Door` (`[house.hpp:Door]`)
- `HouseTransferItem` (`[house.hpp:HouseTransferItem]`)
- `Houses` (`[house.hpp:Houses]`)
- `House` (`[housetile.hpp:House]`)

## Invariants
- None

## Side Effects
- Executes SQL queries against game database (`[house.cpp]`)
- Emits system diagnostic logs (`[house.cpp]`)
- Emits system diagnostic logs (`[housetile.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
