# Bear Room Quest

## Overview
Component package under `scripts/actions/rookgaard/bear_room_quest` containing 2 files (`bear_room_quest_lever.lua`..`bear_room_quest_stone.lua`).

## Interface
- `bearRoomQuestLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [bear_room_quest_lever.lua:bearRoomQuestLever.onUse]
- `Action()` assigned to `bearRoomQuestLever` [bear_room_quest_lever.lua:bearRoomQuestLever]
- `Action()` registration [bear_room_quest_lever.lua:Action]
- `bearStone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [bear_room_quest_stone.lua:bearStone.onUse]
- `Action()` assigned to `bearStone` [bear_room_quest_stone.lua:bearStone]
- `Action()` registration [bear_room_quest_stone.lua:Action]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [bear_room_quest_lever.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [bear_room_quest_stone.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [bear_room_quest_lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [bear_room_quest_lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [bear_room_quest_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [bear_room_quest_stone.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [bear_room_quest_stone.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [bear_room_quest_stone.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
