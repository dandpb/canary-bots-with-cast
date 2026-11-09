# Giant Smithhammer

## Overview
Component package under `scripts/quests/giant_smithhammer` containing 1 files (`lever.lua`..`lever.lua`).

## Interface
- `lever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [lever.lua:lever.onUse]
- `Action()` assigned to `lever` [lever.lua:lever]
- `Action()` registration [lever.lua:Action]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [lever.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
