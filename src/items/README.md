# items

## Overview
Package implementation for `src/items`, providing component logic and data interfaces for items.

## Interface
- `House` (`[bed.hpp:House]`)
- `Player` (`[bed.hpp:Player]`)
- `BedItem` (`[bed.hpp:BedItem]`)
- `getSleeper` (`[bed.hpp:getSleeper]`)
- `setHouse` (`[bed.hpp:setHouse]`)
- `canUse` (`[bed.hpp:canUse]`)
- `isBedComplete` (`[bed.hpp:isBedComplete]`)
- `Item` (`[cylinder.hpp:Item]`)
- `Creature` (`[cylinder.hpp:Creature]`)
- `Cylinder` (`[cylinder.hpp:Cylinder]`)
- Subdirectory [`./containers/README.md`](./containers/README.md) - Sub-package for containers
- Subdirectory [`./decay/README.md`](./decay/README.md) - Sub-package for decay
- Subdirectory [`./functions/README.md`](./functions/README.md) - Sub-package for functions
- Subdirectory [`./weapons/README.md`](./weapons/README.md) - Sub-package for weapons

## Invariants
- Validation assertion: `assert(exclude)` (`[tile.cpp]`)

## Side Effects
- Emits system diagnostic logs (`[bed.cpp]`)
- Schedules timed tasks or dispatcher callbacks (`[bed.cpp]`)
- Emits system diagnostic logs (`[item.cpp]`)
- Emits system diagnostic logs (`[item.hpp]`)
- Emits system diagnostic logs (`[items.cpp]`)
- Emits system diagnostic logs (`[tile.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
