# Katana Quest

## Overview
Component package under `scripts/actions/rookgaard/katana_quest` containing 2 files (`katana_quest_door.lua`..`katana_quest_lever.lua`).

## Interface
- `katanaQuestDoor.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [katana_quest_door.lua:katanaQuestDoor.onUse]
- `Action()` assigned to `katanaQuestDoor` [katana_quest_door.lua:katanaQuestDoor]
- `Action()` registration [katana_quest_door.lua:Action]
- `katanaQuestLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [katana_quest_lever.lua:katanaQuestLever.onUse]
- `Action()` assigned to `katanaQuestLever` [katana_quest_lever.lua:katanaQuestLever]
- `Action()` registration [katana_quest_lever.lua:Action]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [katana_quest_door.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [katana_quest_lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [katana_quest_door.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [katana_quest_door.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [katana_quest_lever.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [katana_quest_lever.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
