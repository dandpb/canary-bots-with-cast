# What A Foolish Quest

## Overview
Component package under `scripts/quests/what_a_foolish_quest` containing 8 files (`action_cat_basket.lua`..`movements_destroy_pies.lua`).

## Interface
- `removeKitty(monsterId)` [action_cat_basket.lua:removeKitty]
- `whatFoolishCat.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_cat_basket.lua:whatFoolishCat.onUse]
- `Action()` assigned to `whatFoolishCat` [action_cat_basket.lua:whatFoolishCat]
- `Action()` registration [action_cat_basket.lua:Action]
- `whatFoolishContract.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_contract.lua:whatFoolishContract.onUse]
- `Action()` assigned to `whatFoolishContract` [action_contract.lua:whatFoolishContract]
- `Action()` registration [action_contract.lua:Action]
- `whatFoolishCrate.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_crate.lua:whatFoolishCrate.onUse]
- `Action()` assigned to `whatFoolishCrate` [action_crate.lua:whatFoolishCrate]
- `Action()` registration [action_crate.lua:Action]
- `whatFoolishCushion.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_cushion.lua:whatFoolishCushion.onUse]
- `Action()` assigned to `whatFoolishCushion` [action_cushion.lua:whatFoolishCushion]
- `Action()` registration [action_cushion.lua:Action]
- `whatFoolishDisguise.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_disguise.lua:whatFoolishDisguise.onUse]
- `Action()` assigned to `whatFoolishDisguise` [action_disguise.lua:whatFoolishDisguise]
- `Action()` registration [action_disguise.lua:Action]
- `whatFoolishWatch.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_watch.lua:whatFoolishWatch.onUse]
- `Action()` assigned to `whatFoolishWatch` [action_watch.lua:whatFoolishWatch]
- `Action()` registration [action_watch.lua:Action]
- `whatFoolishWorn.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_worn_cloth.lua:whatFoolishWorn.onUse]
- `Action()` assigned to `whatFoolishWorn` [action_worn_cloth.lua:whatFoolishWorn]
- `Action()` registration [action_worn_cloth.lua:Action]
- `destroyPies.onStepIn(creature, item, position, fromPosition)` [movements_destroy_pies.lua:destroyPies.onStepIn]
- `MoveEvent()` assigned to `destroyPies` [movements_destroy_pies.lua:destroyPies]
- `MoveEvent()` registration [movements_destroy_pies.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_cat_basket.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_contract.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_crate.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_cushion.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_watch.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_worn_cloth.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_destroy_pies.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_destroy_pies.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_cat_basket.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_cat_basket.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [action_cat_basket.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_cat_basket.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [action_cat_basket.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_contract.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_contract.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_crate.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_crate.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_cushion.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_cushion.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_cushion.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
