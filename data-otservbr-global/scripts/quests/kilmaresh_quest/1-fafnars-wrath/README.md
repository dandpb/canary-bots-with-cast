# 1 Fafnars Wrath

## Overview
Component package under `scripts/quests/kilmaresh_quest/1-fafnars-wrath` containing 4 files (`2-ambassadors-treason.lua`..`8-blessing-the-statues.lua`).

## Interface
- `paper.onUse(player, item, frompos, item2, topos)` [2-ambassadors-treason.lua:paper.onUse]
- `paperScraps.onUse(player, item, frompos, item2, topos)` [2-ambassadors-treason.lua:paperScraps.onUse]
- `scrolls.onUse(player, item, frompos, item2, topos)` [2-ambassadors-treason.lua:scrolls.onUse]
- `roofTop.onStepIn(player, item, frompos, item2, topos)` [2-ambassadors-treason.lua:roofTop.onStepIn]
- `Action()` assigned to `paper` [2-ambassadors-treason.lua:paper]
- `Action()` assigned to `paperScraps` [2-ambassadors-treason.lua:paperScraps]
- `Action()` assigned to `scrolls` [2-ambassadors-treason.lua:scrolls]
- `Action()` registration [2-ambassadors-treason.lua:Action]
- `MoveEvent()` assigned to `roofTop` [2-ambassadors-treason.lua:roofTop]
- `MoveEvent()` registration [2-ambassadors-treason.lua:MoveEvent]
- `potion.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [6-mind-travel.lua:potion.onUse]
- `leftMirror.onStepIn(creature)` [6-mind-travel.lua:leftMirror.onStepIn]
- `rightMirror.onStepIn(creature)` [6-mind-travel.lua:rightMirror.onStepIn]
- `memoryShards.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [6-mind-travel.lua:memoryShards.onUse]
- `energyField.onStepIn(creature, item, position, fromPosition)` [6-mind-travel.lua:energyField.onStepIn]
- `Action()` assigned to `potion` [6-mind-travel.lua:potion]
- `Action()` assigned to `memoryShards` [6-mind-travel.lua:memoryShards]
- `Action()` registration [6-mind-travel.lua:Action]
- `MoveEvent()` assigned to `leftMirror` [6-mind-travel.lua:leftMirror]
- `MoveEvent()` assigned to `rightMirror` [6-mind-travel.lua:rightMirror]
- `MoveEvent()` assigned to `energyField` [6-mind-travel.lua:energyField]
- `MoveEvent()` registration [6-mind-travel.lua:MoveEvent]
- `masksAction.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [7-four-masks.lua:masksAction.onUse]
- `Action()` assigned to `masksAction` [7-four-masks.lua:masksAction]
- `Action()` registration [7-four-masks.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [2-ambassadors-treason.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [6-mind-travel.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [6-mind-travel.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [7-four-masks.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [8-blessing-the-statues.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [2-ambassadors-treason.lua:register]
- Mutates player or global storage state via `setStorageValue` [2-ambassadors-treason.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [6-mind-travel.lua:register]
- Mutates player or global storage state via `setStorageValue` [6-mind-travel.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [6-mind-travel.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [6-mind-travel.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [7-four-masks.lua:register]
- Mutates player or global storage state via `setStorageValue` [7-four-masks.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [7-four-masks.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [8-blessing-the-statues.lua:register]
- Mutates player or global storage state via `setStorageValue` [8-blessing-the-statues.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
