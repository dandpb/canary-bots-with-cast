# Monster Spawns

## Overview
Manages monster spawn zones (`SpawnMonster`, `SpawnsMonster`, `spawnBlock_t`), parsing spawn definitions from XML and scheduling periodic respawn checks and monster placement in the game world.

## Interface
- `spawnBlock_t` (`[spawn_monster.hpp:spawnBlock_t]`): Holds spawn point position, weighted `MonsterType` candidates, interval, direction, and `getMonsterType` / `hasBoss` helpers.
- `SpawnMonster` (`[spawn_monster.hpp:SpawnMonster]`): Manages a single spawn zone (`addMonster`, `removeMonster`, `removeMonsters`, `startup`, `startSpawnMonsterCheck`, `stopEvent`, `isInSpawnMonsterZone`, `cleanup`, `getCenterPos`, `setMonsterVariant`).
- `SpawnsMonster` (`[spawn_monster.hpp:SpawnsMonster]`): Manages all monster spawn zones for a map (`loadFromXML`, `startup`, `clear`, `isStarted`, `isLoaded`, `getspawnMonsterList`, `isInZone`).

## Invariants
- Spawn intervals in `SpawnMonster::addMonster` (`[spawn_monster.cpp:SpawnMonster::addMonster]`) are clamped between `MONSTER_MINSPAWN_INTERVAL` (`1000` ms) and `MONSTER_MAXSPAWN_INTERVAL` (`86400000` ms), and the zone check interval is the greatest common divisor (`std::gcd`) of its monster intervals.
- A boss monster (`monsterType->isBoss()`) cannot share a `spawnBlock_t` with any other monster type (`[spawn_monster.cpp:SpawnMonster::addMonster]`).
- Blockable monsters (`mType->info.isBlockable`) will not respawn while a player without `PlayerFlags_t::IgnoredByMonsters` is within spectator range (`[spawn_monster.cpp:SpawnMonster::checkSpawnMonster]`, `[spawn_monster.cpp:SpawnMonster::findPlayer]`).
- Dispatcher tasks (`startSpawnMonsterCheck`, `checkSpawnMonster`, `scheduleSpawn`) are not scheduled when `g_dispatcher().isShuttingDown()` is true (`[spawn_monster.cpp:SpawnMonster::startSpawnMonsterCheck]`, `[spawn_monster.cpp:SpawnMonster::checkSpawnMonster]`, `[spawn_monster.cpp:SpawnMonster::scheduleSpawn]`).

## Side Effects
- `SpawnsMonster::loadFromXML` (`[spawn_monster.cpp:SpawnsMonster::loadFromXML]`): Reads the monster spawn XML file from disk.
- `SpawnMonster::spawnMonster` (`[spawn_monster.cpp:SpawnMonster::spawnMonster]`): Instantiates `Monster` objects, places them on the map via `g_game().internalPlaceCreature` or `g_game().placeCreature`, and triggers `monster->onSpawn(sb.pos)`.
- `SpawnMonster::startSpawnMonsterCheck` and `SpawnMonster::scheduleSpawn` (`[spawn_monster.cpp:SpawnMonster::startSpawnMonsterCheck]`, `[spawn_monster.cpp:SpawnMonster::scheduleSpawn]`): Schedule recurring/delayed tasks on `g_dispatcher()` and emit `CONST_ME_TELEPORT` effects via `g_game().addMagicEffect`.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
