# Map Zones (`src/game/zones`)

## Overview
Manages named and ID-indexed spatial zones (`Zone` and `Area`) across the game map, maintaining weak-reference caches of creatures, players, monsters, NPCs, and items within each zone and supporting bulk entity removal, monster variant overrides, and XML loading.

## Interface
- `Area` & `Area::PositionIterator` (`[zone.hpp:Area]`, `[zone.hpp:Area::PositionIterator]`): 3D axis-aligned bounding box (`from`, `to`) supporting `intersects`, `contains`, and 3D coordinate iteration (`begin`, `end`).
- `weak::ThingHasher`, `weak::ThingComparator`, `weak::set<T>`, `weak::lock<T>` (`[zone.hpp:weak::ThingHasher]`, `[zone.hpp:weak::ThingComparator]`, `[zone.hpp:weak::lock]`): Weak-pointer hash set utilities that automatically prune expired pointers when locked.
- `Zone` (`[zone.hpp:Zone]`): Spatial zone registry and instance controller (`addZone`, `getZone`, `getZones`, `clearZones`, `refreshAll`, `loadFromXML`, `addArea`, `subtractArea`, `addPosition`, `removePosition`, `getRemoveDestination`, `setRemoveDestination`, `getPositions`, `getCreatures`, `getPlayers`, `getMonsters`, `getNpcs`, `getItems`, `creatureAdded`, `creatureRemoved`, `thingAdded`, `itemAdded`, `itemRemoved`, `removePlayers`, `removeMonsters`, `removeNpcs`, `refresh`, `setMonsterVariant`, `isStatic`).

## Invariants
- `Zone::addZone` reserves the name `"default"` (returning `nullptr`) and rejects duplicate zone names; if a non-zero `zoneID` already exists in `zonesByID` (e.g., pre-created during map tile loading via `getZone(uint32_t)`), `addZone` links the name to the existing `Zone` instance (`[zone.cpp:Zone::addZone]`, `[zone.cpp:Zone::getZone]`).
- Zones with `id != 0` (`isStatic() == true`, loaded from map/OTBM) are preserved across `Zone::clearZones()`, whereas dynamically created Lua zones (`id == 0`) are cleared and refreshed (`[zone.hpp:Zone::isStatic]`, `[zone.cpp:Zone::clearZones]`).
- `Zone::getRemoveDestination` falls back to the player's town temple position when `removeDestination` is default-constructed `(0, 0, 0)` (`[zone.cpp:Zone::getRemoveDestination]`).

## Side Effects
- Mutates process-wide static hash maps `Zone::zones` and `Zone::zonesByID` (`[zone.cpp:Zone::addZone]`, `[zone.cpp:Zone::getZone]`, `[zone.cpp:Zone::clearZones]`).
- `Zone::refresh` clears all entity caches (`creaturesCache`, `monstersCache`, `npcsCache`, `playersCache`, `itemsCache`) and triggers `g_game().map.refreshZones(position)` for every position in the zone (`[zone.cpp:Zone::refresh]`).
- `Zone::removePlayers` teleports all players in the zone to `getRemoveDestination(player)` via `g_game().internalTeleport` and strips the `"goshnars-hatred-damage"` icon; `removeMonsters` and `removeNpcs` despawn entities via `g_game().removeCreature` (`[zone.cpp:Zone::removePlayers]`, `[zone.cpp:Zone::removeMonsters]`, `[zone.cpp:Zone::removeNpcs]`).
- `Zone::setMonsterVariant` updates `SpawnMonster::setMonsterVariant` for all monster spawns centered inside the zone and removes existing monsters (`[zone.cpp:Zone::setMonsterVariant]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
