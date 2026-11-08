# Hunter Outfits Quest

## Overview
Component package under `scripts/quests/hunter_outfits_quest` containing 2 files (`action_all_hymn_piano_teleport.lua`..`action_music_sheet.lua`).

## Interface
- `hunterAll.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_all_hymn_piano_teleport.lua:hunterAll.onUse]
- `Action()` assigned to `hunterAll` [action_all_hymn_piano_teleport.lua:hunterAll]
- `Action()` registration [action_all_hymn_piano_teleport.lua:Action]
- `hunterMusic.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_music_sheet.lua:hunterMusic.onUse]
- `Action()` assigned to `hunterMusic` [action_music_sheet.lua:hunterMusic]
- `Action()` registration [action_music_sheet.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_all_hymn_piano_teleport.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_music_sheet.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_all_hymn_piano_teleport.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [action_all_hymn_piano_teleport.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_music_sheet.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_music_sheet.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_music_sheet.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
