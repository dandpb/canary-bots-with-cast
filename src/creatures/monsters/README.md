# Monsters

## Overview
Implements monster instances (`Monster`), monster type definitions and spell deserialization (`MonsterType`, `MonsterSpell`, `Monsters`), and coordinates with monster spawn zones (`spawns`).

## Interface
- `Monster` (`[monster.hpp:Monster]`): Concrete `Creature` subclass implementing monster AI, targeting (`searchTarget`, `selectTarget`, `updateTargetList`), pathfinding/pushing (`getNextStep`, `pushItem`, `pushItems`, `pushCreature`, `pushCreatures`), combat (`doAttacking`, `blockHit`, `drainHealth`, `changeHealth`), loot generation (`dropLoot`), Hazard system, SoulPit, and Forge (`configureForgeSystem`, `applyStacks`) mechanics.
- `MonsterType`, `MonsterSpell`, `Loot`, `spellBlock_t` (`[monsters.hpp:MonsterType]`, `[monsters.hpp:MonsterSpell]`, `[monsters.hpp:Loot]`, `[monsters.hpp:spellBlock_t]`): Defines static monster properties, immunities, bestiary/bosstiary metadata, loot tables (`loadLoot`), and day/night spawn checks (`canSpawn`).
- `Monsters` (`[monsters.hpp:Monsters]`, `[monsters.hpp:g_monsters]`): Singleton registry of `MonsterType` definitions (`getMonsterType`, `getMonsterTypeByRaceId`, `tryAddMonsterType`, `deserializeSpell`, `getMonstersByRace`, `getMonstersByBestiaryStars`, `clear`).
- [spawns](./spawns/README.md): Monster spawn zone definitions and respawn scheduling (`SpawnMonster`, `SpawnsMonster`).

## Invariants
- `Monster::setID` (`[monster.cpp:Monster::setID]`) assigns unique IDs starting from `Monster::monsterAutoID` (`0x50000001`).
- `MonsterType::canSpawn` (`[monsters.cpp:MonsterType::canSpawn]`) enforces day/night respawn period restrictions on surface layers (`pos.z <= MAP_INIT_SURFACE_LAYER`), ignoring them underground when `info.respawnType.underground` is true.
- `Monster::isPushable` (`[monster.cpp:Monster::isPushable]`) requires both `m_monsterType->info.pushable` and `baseSpeed != 0`.

## Side Effects
- Registers/removes monsters in the global game state (`g_game().addMonster`, `g_game().removeMonster`) and notifies spectators on name/health/tile updates (`[monster.cpp:Monster::addList]`, `[monster.cpp:Monster::removeList]`, `[monster.cpp:Monster::setName]`).
- Pushes blocking items and creatures across tiles (`[monster.hpp:Monster::pushItems]`, `[monster.hpp:Monster::pushCreatures]`), executes monster attacks/spells, and spawns corpses and loot on death (`[monster.hpp:Monster::death]`, `[monster.hpp:Monster::dropLoot]`).
- `Monsters::deserializeSpell` (`[monsters.cpp:Monsters::deserializeSpell]`): Allocates `Combat`, `AreaCombat`, and `Condition` instances for monster spell blocks.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
