# World Position & Teleport Movement (`src/game/movement`)

## Overview
Defines 3D map coordinates (`Position`), cardinal/diagonal movement directions (`Direction`), and the `Teleport` tile item/cylinder that relocates creatures and items stepping onto or placed into it.

## Interface
- `Direction` (`[position.hpp:Direction]`): Cardinal and diagonal movement direction enumeration (`DIRECTION_NORTH` through `DIRECTION_NONE`).
- `Position` (`[position.hpp:Position]`): 3D coordinate struct (`x`, `y`, `z`) providing range checks (`areInRange`), offsets (`getOffsetX/Y/Z`), Manhattan/diagonal/Euclidean distance calculations (`getDistanceX/Y/Z`, `getDiagonalDistance`, `getEuclideanDistance`), `getRandomDirection()`, comparison/arithmetic operators, `std::hash<Position>`, and `fmt::formatter<Position>`.
- `Teleport` (`[teleport.hpp:Teleport]`): Final class inheriting `Item` and `Cylinder` that serializes `ATTR_TELE_DEST` (`readAttr`, `serializeAttr`), manages destination coordinates (`getDestPos`, `setDestPos`), detects teleport cycles (`checkInfinityLoop`), and intercepts `addThing` to teleport creatures and items.

## Invariants
- `Teleport::addThing` ignores teleports with an unconfigured destination `(0, 0, 0)` or a missing destination tile (`[teleport.cpp:Teleport::addThing]`).
- `Teleport::checkInfinityLoop` recursively traverses destination teleports and aborts `Teleport::addThing` if a cycle back to `getPosition()` is detected (`[teleport.cpp:Teleport::checkInfinityLoop]`, `[teleport.cpp:Teleport::addThing]`).
- `Teleport::queryAdd` and `Teleport::queryMaxCount` always return `RETURNVALUE_NOTPOSSIBLE` (`[teleport.cpp:Teleport::queryAdd]`, `[teleport.cpp:Teleport::queryMaxCount]`).

## Side Effects
- `Teleport::addThing` turns and moves creatures across map tiles (`g_game().internalCreatureTurn`, `g_game().map.moveCreature`), moves items (`g_game().internalMoveItem`), and dispatches visual magic effects (`g_game().addMagicEffect`) (`[teleport.cpp:Teleport::addThing]`).
- `Position::getRandomDirection` shuffles a static direction vector using the global RNG (`getRandomGenerator()`) (`[position.cpp:Position::getRandomDirection]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
