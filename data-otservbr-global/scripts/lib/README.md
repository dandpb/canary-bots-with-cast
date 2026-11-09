# Lib

## Overview
Component package under `scripts/lib` containing 2 files (`monster_functions.lua`..`register_actions.lua`).

## Interface
- `Monster:handleCobraOnSpawn()` [monster_functions.lua:Monster:handleCobraOnSpawn]
- `revertItem(position, itemId, transformId)` [register_actions.lua:revertItem]
- `removeRemains(toPosition)` [register_actions.lua:removeRemains]
- `revertCask(position)` [register_actions.lua:revertCask]
- `addFerumbrasAscendantReward(player, target, toPosition)` [register_actions.lua:addFerumbrasAscendantReward]
- `onDestroyItem(player, item, fromPosition, target, toPosition, isHotkey)` [register_actions.lua:onDestroyItem]
- `onUseRope(player, item, fromPosition, target, toPosition, isHotkey)` [register_actions.lua:onUseRope]
- `onUseShovel(player, item, fromPosition, target, toPosition, isHotkey)` [register_actions.lua:onUseShovel]
- `onUsePick(player, item, fromPosition, target, toPosition, isHotkey)` [register_actions.lua:onUsePick]
- `onUseMachete(player, item, fromPosition, target, toPosition, isHotkey)` [register_actions.lua:onUseMachete]
- `onUseCrowbar(player, item, fromPosition, target, toPosition, isHotkey)` [register_actions.lua:onUseCrowbar]
- `onUseSpoon(player, item, fromPosition, target, toPosition, isHotkey)` [register_actions.lua:onUseSpoon]
- `onUseSpikedSquelcher(player, item, fromPosition, target, toPosition, isHotkey)` [register_actions.lua:onUseSpikedSquelcher]
- `onUseScythe(player, item, fromPosition, target, toPosition, isHotkey)` [register_actions.lua:onUseScythe]
- `onUseKitchenKnife(player, item, fromPosition, target, toPosition, isHotkey)` [register_actions.lua:onUseKitchenKnife]
- `onGrindItem(player, item, fromPosition, target, toPosition)` [register_actions.lua:onGrindItem]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [monster_functions.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [register_actions.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [register_actions.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [register_actions.lua:Tile]

## Side Effects
- Mutates player or global storage state via `setStorageValue` [monster_functions.lua:setStorageValue]
- Mutates player or global storage state via `setStorageValue` [register_actions.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [register_actions.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [register_actions.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [register_actions.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [register_actions.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
