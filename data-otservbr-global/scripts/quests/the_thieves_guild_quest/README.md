# The Thieves Guild Quest

## Overview
Component package under `scripts/quests/the_thieves_guild_quest` containing 5 files (`actions_climbing_vine.lua`..`actions_note.lua`).

## Interface
- `theThievesVine.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_climbing_vine.lua:theThievesVine.onUse]
- `Action()` assigned to `theThievesVine` [actions_climbing_vine.lua:theThievesVine]
- `Action()` registration [actions_climbing_vine.lua:Action]
- `theThievesKit.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_dwarf_disguise_kit.lua:theThievesKit.onUse]
- `Action()` assigned to `theThievesKit` [actions_dwarf_disguise_kit.lua:theThievesKit]
- `Action()` registration [actions_dwarf_disguise_kit.lua:Action]
- `theThievesDoor.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_fish_napping_door.lua:theThievesDoor.onUse]
- `Action()` assigned to `theThievesDoor` [actions_fish_napping_door.lua:theThievesDoor]
- `Action()` registration [actions_fish_napping_door.lua:Action]
- `theThievesKey.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_fish_napping_key.lua:theThievesKey.onUse]
- `Action()` assigned to `theThievesKey` [actions_fish_napping_key.lua:theThievesKey]
- `Action()` registration [actions_fish_napping_key.lua:Action]
- `removeNote(position)` [actions_note.lua:removeNote]
- `theThievesNote.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_note.lua:theThievesNote.onUse]
- `Action()` assigned to `theThievesNote` [actions_note.lua:theThievesNote]
- `Action()` registration [actions_note.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_fish_napping_door.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_fish_napping_key.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_note.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_note.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_climbing_vine.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_climbing_vine.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_dwarf_disguise_kit.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_dwarf_disguise_kit.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_fish_napping_door.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_fish_napping_door.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_fish_napping_key.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_fish_napping_key.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_fish_napping_key.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_note.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_note.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_note.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
