# Rookgaard

## Overview
Provides 4 direct files (`chest.lua`..`sewer_lever.lua`) and 2 subdirectories under `scripts/actions/rookgaard`.

## Interface
- `chest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [chest.lua:chest.onUse]
- `Action()` assigned to `chest` [chest.lua:chest]
- `Action()` registration [chest.lua:Action]
- `goblintemple1Quest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [goblin_temple_quest.lua:goblintemple1Quest.onUse]
- `goblintemple2Quest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [goblin_temple_quest.lua:goblintemple2Quest.onUse]
- `Action()` assigned to `goblintemple1Quest` [goblin_temple_quest.lua:goblintemple1Quest]
- `Action()` assigned to `goblintemple2Quest` [goblin_temple_quest.lua:goblintemple2Quest]
- `Action()` registration [goblin_temple_quest.lua:Action]
- `rapierQuest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [rapier_quest.lua:rapierQuest.onUse]
- `Action()` assigned to `rapierQuest` [rapier_quest.lua:rapierQuest]
- `Action()` registration [rapier_quest.lua:Action]
- `moveToPosition(self, toPosition, pushMove, monsterPosition)` [sewer_lever.lua:moveToPosition]
- `sewerLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [sewer_lever.lua:sewerLever.onUse]
- `Action()` assigned to `sewerLever` [sewer_lever.lua:sewerLever]
- `Action()` registration [sewer_lever.lua:Action]
- [bear_room_quest](./bear_room_quest/README.md) - Component package under `scripts/actions/rookgaard/bear_room_quest` containing 2 files (`bear_room_quest_lever.lua`..`bear_room_quest_stone.lua`).
- [katana_quest](./katana_quest/README.md) - Component package under `scripts/actions/rookgaard/katana_quest` containing 2 files (`katana_quest_door.lua`..`katana_quest_lever.lua`).

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [chest.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [sewer_lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [chest.lua:register]
- Mutates player or global storage state via `setStorageValue` [chest.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [chest.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [goblin_temple_quest.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [goblin_temple_quest.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [rapier_quest.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [rapier_quest.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [sewer_lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [sewer_lever.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [sewer_lever.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [sewer_lever.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
