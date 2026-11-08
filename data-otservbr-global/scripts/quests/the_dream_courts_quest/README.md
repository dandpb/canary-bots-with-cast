# The Dream Courts Quest

## Overview
Component package under `scripts/quests/the_dream_courts_quest` containing 36 files (`actions_acidFishingRod.lua`..`movements_spiderSummon.lua`).

## Interface
- Defines 36 script/configuration files (`actions_acidFishingRod.lua` through `movements_spiderSummon.lua`) [actions_acidFishingRod.lua]
- `actions_acidFishingRod.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_acidFishingRod.lua:actions_acidFishingRod.onUse]
- `Action()` assigned to `actions_acidFishingRod` [actions_acidFishingRod.lua:actions_acidFishingRod]
- `Action()` registration [actions_acidFishingRod.lua:Action]
- `actions_bookOnTable.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bookOnTable.lua:actions_bookOnTable.onUse]
- `Action()` assigned to `actions_bookOnTable` [actions_bookOnTable.lua:actions_bookOnTable]
- `Action()` registration [actions_bookOnTable.lua:Action]
- `revertStone(position, on, off)` [actions_chargedCompass.lua:revertStone]
- `actions_chargedCompass.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_chargedCompass.lua:actions_chargedCompass.onUse]
- `Action()` assigned to `actions_chargedCompass` [actions_chargedCompass.lua:actions_chargedCompass]
- `Action()` registration [actions_chargedCompass.lua:Action]
- `actions_colourfulMushroom.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_colourfulMushroom.lua:actions_colourfulMushroom.onUse]
- `Action()` assigned to `actions_colourfulMushroom` [actions_colourfulMushroom.lua:actions_colourfulMushroom]
- `Action()` registration [actions_colourfulMushroom.lua:Action]
- `actions_containerRewards.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_containerRewards.lua:actions_containerRewards.onUse]
- `Action()` assigned to `actions_containerRewards` [actions_containerRewards.lua:actions_containerRewards]
- `Action()` registration [actions_containerRewards.lua:Action]
- `actions_doorInvisible.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_doorInvisible.lua:actions_doorInvisible.onUse]
- `Action()` assigned to `actions_doorInvisible` [actions_doorInvisible.lua:actions_doorInvisible]
- `Action()` registration [actions_doorInvisible.lua:Action]
- `revertStone(position, on, off)` [actions_dreamTalisman.lua:revertStone]
- `actions_dreamTalisman.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_dreamTalisman.lua:actions_dreamTalisman.onUse]
- `Action()` assigned to `actions_dreamTalisman` [actions_dreamTalisman.lua:actions_dreamTalisman]
- `Action()` registration [actions_dreamTalisman.lua:Action]
- `placeMask(position, wmask, nmask)` [actions_dreamcatcher_curse.lua:placeMask]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_acidFishingRod.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_bookOnTable.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_chargedCompass.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_chargedCompass.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_colourfulMushroom.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_containerRewards.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_doorInvisible.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_dreamTalisman.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_dreamTalisman.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_dreamcatcher_curse.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_dreamcatcher_curse.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_dreamcatcher_curse.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_acidFishingRod.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_acidFishingRod.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bookOnTable.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_bookOnTable.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_bookOnTable.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_chargedCompass.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_chargedCompass.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_chargedCompass.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_chargedCompass.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_colourfulMushroom.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_colourfulMushroom.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_colourfulMushroom.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
