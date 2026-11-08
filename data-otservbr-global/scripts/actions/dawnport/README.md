# Dawnport

## Overview
Component package under `scripts/actions/dawnport` containing 2 files (`lever.lua`..`vocation_door.lua`).

## Interface
- `lever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [lever.lua:lever.onUse]
- `Action()` assigned to `lever` [lever.lua:lever]
- `Action()` registration [lever.lua:Action]
- `vocationDoor.onUse(player, item, target, position, fromPosition)` [vocation_door.lua:vocationDoor.onUse]
- `Action()` assigned to `vocationDoor` [vocation_door.lua:vocationDoor]
- `Action()` registration [vocation_door.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [lever.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [vocation_door.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [lever.lua:register]
- Mutates player or global storage state via `setStorageValue` [lever.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [lever.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [lever.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [lever.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [vocation_door.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [vocation_door.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
