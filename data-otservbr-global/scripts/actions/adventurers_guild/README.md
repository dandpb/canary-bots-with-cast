# Adventurers Guild

## Overview
Component package under `scripts/actions/adventurers_guild` containing 2 files (`adventurers_stone.lua`..`magic_door.lua`).

## Interface
- `doNotTeleport(player)` [adventurers_stone.lua:doNotTeleport]
- `adventurersStone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [adventurers_stone.lua:adventurersStone.onUse]
- `Action()` assigned to `adventurersStone` [adventurers_stone.lua:adventurersStone]
- `Action()` registration [adventurers_stone.lua:Action]
- `magicDoor.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [magic_door.lua:magicDoor.onUse]
- `Action()` assigned to `magicDoor` [magic_door.lua:magicDoor]
- `Action()` registration [magic_door.lua:Action]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [adventurers_stone.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [magic_door.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [adventurers_stone.lua:register]
- Mutates player or global storage state via `setStorageValue` [adventurers_stone.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [adventurers_stone.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [magic_door.lua:register]
- Mutates player or global storage state via `setStorageValue` [magic_door.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [magic_door.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
