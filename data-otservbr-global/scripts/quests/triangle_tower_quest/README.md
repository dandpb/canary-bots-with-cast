# Triangle Tower Quest

## Overview
Component package under `scripts/quests/triangle_tower_quest` containing 1 files (`actions_triangle_tower_lever.lua`..`actions_triangle_tower_lever.lua`).

## Interface
- `othersTriangle.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_triangle_tower_lever.lua:othersTriangle.onUse]
- `Action()` assigned to `othersTriangle` [actions_triangle_tower_lever.lua:othersTriangle]
- `Action()` registration [actions_triangle_tower_lever.lua:Action]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_triangle_tower_lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_triangle_tower_lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_triangle_tower_lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_triangle_tower_lever.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
