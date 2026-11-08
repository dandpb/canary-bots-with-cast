# Mintwallin Quest

## Overview
Component package under `scripts/quests/mintwallin_quest` containing 1 files (`actions_devil_helmet_lever.lua`..`actions_devil_helmet_lever.lua`).

## Interface
- `devilHelmetLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_devil_helmet_lever.lua:devilHelmetLever.onUse]
- `Action()` assigned to `devilHelmetLever` [actions_devil_helmet_lever.lua:devilHelmetLever]
- `Action()` registration [actions_devil_helmet_lever.lua:Action]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_devil_helmet_lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_devil_helmet_lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_devil_helmet_lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_devil_helmet_lever.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
