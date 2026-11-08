# Desert Dungeon Quest

## Overview
Component package under `scripts/quests/desert_dungeon_quest` containing 1 files (`actions_desert_dungeon_lever.lua`..`actions_desert_dungeon_lever.lua`).

## Interface
- `othersDesert.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_desert_dungeon_lever.lua:othersDesert.onUse]
- `Action()` assigned to `othersDesert` [actions_desert_dungeon_lever.lua:othersDesert]
- `Action()` registration [actions_desert_dungeon_lever.lua:Action]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_desert_dungeon_lever.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_desert_dungeon_lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_desert_dungeon_lever.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_desert_dungeon_lever.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_desert_dungeon_lever.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
