# Other

## Overview
Provides 29 direct files (`baking.lua`..`world_board.lua`) and 1 subdirectories under `scripts/actions/other`.

## Interface
- Defines 29 script/configuration files (`baking.lua` through `world_board.lua`) [baking.lua]
- `baking.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [baking.lua:baking.onUse]
- `Action()` assigned to `baking` [baking.lua:baking]
- `Action()` registration [baking.lua:Action]
- `birdcage.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [birdcage.lua:birdcage.onUse]
- `Action()` assigned to `birdcage` [birdcage.lua:birdcage]
- `Action()` registration [birdcage.lua:Action]
- `catchFish.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [catch_fish.lua:catchFish.onUse]
- `Action()` assigned to `catchFish` [catch_fish.lua:catchFish]
- `Action()` registration [catch_fish.lua:Action]
- `constructionKit.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [construction_kits.lua:constructionKit.onUse]
- `Action()` assigned to `constructionKit` [construction_kits.lua:constructionKit]
- `Action()` registration [construction_kits.lua:Action]
- `createSugarOat.onUse(cid, item, fromPosition, itemEx, toPosition, isHotkey)` [create_sugar_oat.lua:createSugarOat.onUse]
- `Action()` assigned to `createSugarOat` [create_sugar_oat.lua:createSugarOat]
- `Action()` registration [create_sugar_oat.lua:Action]
- `removeEntrance()` [destroy.lua:removeEntrance]
- `destroy.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [destroy.lua:destroy.onUse]
- `Action()` assigned to `destroy` [destroy.lua:destroy]
- `Action()` registration [destroy.lua:Action]
- `downFloor.onUse(player, item, fromPosition, itemEx, toPosition)` [down_floor.lua:downFloor.onUse]
- `Action()` assigned to `downFloor` [down_floor.lua:downFloor]
- `Action()` registration [down_floor.lua:Action]
- `dryadAction.onUse(player, item, target, position, fromPosition)` [dryad_garden.lua:dryadAction.onUse]
- `Action()` assigned to `dryadAction` [dryad_garden.lua:dryadAction]
- [others](./others/README.md) - Component package under `scripts/actions/other/others` containing 2 files (`quest_system1.lua`..`quest_system2.lua`).

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [construction_kits.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [construction_kits.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [destroy.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [destroy.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [enchanting.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [fishing.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [fishing.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [fluids.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [fluids.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [gems.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [gems.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [kits.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [baking.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [baking.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [birdcage.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [birdcage.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [catch_fish.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [catch_fish.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [construction_kits.lua:register]
- Mutates player or global storage state via `setStorageValue` [construction_kits.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [construction_kits.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [construction_kits.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [create_sugar_oat.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [create_sugar_oat.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
