# Prison

## Overview
Component package under `scripts/actions/roshamuul/prison` containing 2 files (`golden.lua`..`keys.lua`).

## Interface
- `golden.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [golden.lua:golden.onUse]
- `Action()` assigned to `golden` [golden.lua:golden]
- `Action()` registration [golden.lua:Action]
- `keys.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [keys.lua:keys.onUse]
- `Action()` assigned to `keys` [keys.lua:keys]
- `Action()` registration [keys.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [golden.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [golden.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [golden.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [keys.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [keys.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [golden.lua:register]
- Mutates player or global storage state via `setStorageValue` [golden.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [golden.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [golden.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [golden.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [golden.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [keys.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [keys.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [keys.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [keys.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [keys.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
