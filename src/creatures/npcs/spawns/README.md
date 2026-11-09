# NPC Spawns

## Overview
Manages non-player character spawn zones (`SpawnNpc`, `SpawnsNpc`, `spawnBlockNpc_t`), loading NPC spawn definitions from XML and scheduling NPC placement and periodic respawn checks.

## Interface
- `spawnBlockNpc_t` (`[spawn_npc.hpp:spawnBlockNpc_t]`): Stores an NPC spawn entry (`pos`, `npcType`, `lastSpawnNpc`, `interval`, `direction`).
- `SpawnNpc` (`[spawn_npc.hpp:SpawnNpc]`): Manages an individual NPC spawn zone (`addNpc`, `removeNpc`, `getInterval`, `startup`, `startSpawnNpcCheck`, `stopEvent`, `isInSpawnNpcZone`, `cleanup`).
- `SpawnsNpc` (`[spawn_npc.hpp:SpawnsNpc]`): Manages the collection of NPC spawn zones (`loadFromXml`, `startup`, `clear`, `isStarted`, `setStarted`, `isLoaded`, `setLoaded`, `setFileName`, `getSpawnNpcList`, `isInZone`).

## Invariants
- `SpawnsNpc::loadFromXml` (`[spawn_npc.cpp:SpawnsNpc::loadFromXml]`) only accepts NPC `spawntime` intervals between `MINSPAWN_INTERVAL` (`1000` ms) and `MAXSPAWN_INTERVAL` (`86400000` ms).
- `SpawnNpc::checkSpawnNpc` (`[spawn_npc.cpp:SpawnNpc::checkSpawnNpc]`) defers respawning if a player without `PlayerFlags_t::IgnoredByNpcs` is within spectator range (`findPlayer(pos)`).
- Dispatcher tasks (`checkSpawnNpc`, `scheduleSpawnNpc`) are skipped when `g_dispatcher().isShuttingDown()` is true (`[spawn_npc.cpp:SpawnNpc::checkSpawnNpc]`, `[spawn_npc.cpp:SpawnNpc::scheduleSpawnNpc]`).

## Side Effects
- `SpawnsNpc::loadFromXml` (`[spawn_npc.cpp:SpawnsNpc::loadFromXml]`): Reads the NPC spawn XML file from disk.
- `SpawnNpc::spawnNpc` (`[spawn_npc.cpp:SpawnNpc::spawnNpc]`): Instantiates `Npc` objects and places them in the world via `g_game().internalPlaceCreature` or `g_game().placeCreature`.
- `SpawnNpc::startSpawnNpcCheck` and `SpawnNpc::scheduleSpawnNpc` (`[spawn_npc.cpp:SpawnNpc::startSpawnNpcCheck]`, `[spawn_npc.cpp:SpawnNpc::scheduleSpawnNpc]`): Schedule events on `g_dispatcher()` and emit `CONST_ME_TELEPORT` effects via `g_game().addMagicEffect`.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
