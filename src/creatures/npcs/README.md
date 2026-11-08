# NPCs

## Overview
Implements non-player character instances (`Npc`), static NPC type definitions and shop item registries (`NpcType`, `Shop`, `Npcs`), and coordinates with NPC spawn zones (`spawns`).

## Interface
- `Npc` (`[npc.hpp:Npc]`): Concrete `Creature` subclass handling player interaction states (`setPlayerInteraction`, `removePlayerInteraction`, `resetPlayerInteractions`, `isInteractingWithPlayer`, `isPlayerInteractingOnTopic`, `canInteract`), NPC shop windows (`addShopPlayer`, `removeShopPlayer`, `closeAllShopWindows`, `onPlayerBuyItem`, `onPlayerSellItem`, `onPlayerSellAllLoot`, `onPlayerCheckItem`), movement (`getNextStep`, `canWalkTo`), and Lua creature callbacks.
- `NpcType`, `Shop` (`[npcs.hpp:NpcType]`, `[npcs.hpp:Shop]`): Stores NPC metadata, Lua event IDs (`loadCallback`), shop item lists (`loadShop`, `getCurrencyId`, `getShopItems`), and day/night spawn checks (`canSpawn`).
- `Npcs` (`[npcs.hpp:Npcs]`, `[npcs.hpp:g_npcs]`): Singleton registry of `NpcType` definitions (`getNpcType`, `getNpcTypes`, `load`, `reload`).
- [spawns](./spawns/README.md): NPC spawn zone definitions and respawn scheduling (`SpawnNpc`, `SpawnsNpc`).

## Invariants
- `Npc::setID` (`[npc.cpp:Npc::setID]`) assigns unique IDs starting from `Npc::npcAutoID` (`0x80000000`).
- `Npc::isAttackable` (`[npc.cpp:Npc::isAttackable]`) always returns `false`, and `Npc::canSeeInvisibility` (`[npc.cpp:Npc::canSeeInvisibility]`) always returns `true`.
- `Npc::canInteract` (`[npc.cpp:Npc::canInteract]`) requires the target position to be on the same `z` floor and within `Creature::canSee` range (default `4`).
- `NpcType::getCurrencyId`, `NpcType::getShopItems`, and `Npcs::getNpcTypes` (`[npcs.hpp:NpcType::getCurrencyId]`, `[npcs.hpp:NpcType::getShopItems]`, `[npcs.hpp:Npcs::getNpcTypes]`) are inline read-only accessors preserving ABI/layout compatibility for the bot `.so` hot-reload engine.

## Side Effects
- Registers/removes NPCs in `g_game()` (`[npc.cpp:Npc::addList]`, `[npc.cpp:Npc::removeList]`) and triggers `spawnNpc->startSpawnNpcCheck()` when an NPC is removed (`[npc.cpp:Npc::onRemoveCreature]`).
- `NpcType::loadShop` (`[npcs.cpp:NpcType::loadShop]`): Mutates global `Item::items` buy/sell prices (`iType.sellPrice`, `iType.buyPrice`) when higher than existing prices.
- `Npcs::load` and `Npcs::reload` (`[npcs.cpp:Npcs::load]`, `[npcs.cpp:Npcs::reload]`): Load Lua NPC libraries (`<CORE_DIRECTORY>/npclib/load.lua`) and scripts (`<DATA_DIRECTORY>/npc`), and reset active NPCs via `g_game().resetNpcs()`.
- Invokes Lua callbacks via `CreatureCallback` on creature appear, disappear, move, say, think, and shop transactions (`[npc.cpp:Npc::onCreatureAppear]`, `[npc.cpp:Npc::onRemoveCreature]`, `[npc.cpp:Npc::onCreatureMove]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
