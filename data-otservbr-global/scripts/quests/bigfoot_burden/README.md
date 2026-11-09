# Bigfoot Burden

## Overview
Component package under `scripts/quests/bigfoot_burden` containing 29 files (`actions_beer.lua`..`movements_warzone_teleport.lua`).

## Interface
- Defines 29 script/configuration files (`actions_beer.lua` through `movements_warzone_teleport.lua`) [actions_beer.lua]
- `bigfootBeer.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_beer.lua:bigfootBeer.onUse]
- `Action()` assigned to `bigfootBeer` [actions_beer.lua:bigfootBeer]
- `Action()` registration [actions_beer.lua:Action]
- `returnCrystal(position, id)` [actions_crystal.lua:returnCrystal]
- `bigfootCrystal.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_crystal.lua:bigfootCrystal.onUse]
- `Action()` assigned to `bigfootCrystal` [actions_crystal.lua:bigfootCrystal]
- `Action()` registration [actions_crystal.lua:Action]
- `bigfootExtractor.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_extractor.lua:bigfootExtractor.onUse]
- `Action()` assigned to `bigfootExtractor` [actions_extractor.lua:bigfootExtractor]
- `Action()` registration [actions_extractor.lua:Action]
- `bigfootMatch.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_matchmaker.lua:bigfootMatch.onUse]
- `Action()` assigned to `bigfootMatch` [actions_matchmaker.lua:bigfootMatch]
- `Action()` registration [actions_matchmaker.lua:Action]
- `bigfootPiece.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mouthpiece.lua:bigfootPiece.onUse]
- `Action()` assigned to `bigfootPiece` [actions_mouthpiece.lua:bigfootPiece]
- `Action()` registration [actions_mouthpiece.lua:Action]
- `revertAid(position)` [actions_mushroom.lua:revertAid]
- `bigfootMushroom.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mushroom.lua:bigfootMushroom.onUse]
- `Action()` assigned to `bigfootMushroom` [actions_mushroom.lua:bigfootMushroom]
- `Action()` registration [actions_mushroom.lua:Action]
- `bigfootMusic.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_music.lua:bigfootMusic.onUse]
- `Action()` assigned to `bigfootMusic` [actions_music.lua:bigfootMusic]
- `Action()` registration [actions_music.lua:Action]
- `bigfootPackage.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_package.lua:bigfootPackage.onUse]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_beer.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_crystal.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_crystal.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_extractor.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_matchmaker.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mouthpiece.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_mushroom.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_music.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_pig.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_repair.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_rewards.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_shooting.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_beer.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_beer.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_beer.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_crystal.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_crystal.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_crystal.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_crystal.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_extractor.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_extractor.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_extractor.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_matchmaker.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_matchmaker.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
