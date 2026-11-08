# The Cursed Crystal

## Overview
Component package under `scripts/quests/the_cursed_crystal` containing 4 files (`actions_MedusaOil.lua`..`movements_StepIn_CursedCrystal.lua`).

## Interface
- `theCursedMedusa.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_MedusaOil.lua:theCursedMedusa.onUse]
- `Action()` assigned to `theCursedMedusa` [actions_MedusaOil.lua:theCursedMedusa]
- `Action()` registration [actions_MedusaOil.lua:Action]
- `isInArea(pos, fromPos, toPos)` [actions_Misc.lua:isInArea]
- `hasValidItem(position)` [actions_Misc.lua:hasValidItem]
- `isVortexInArea(fromPos, toPos)` [actions_Misc.lua:isVortexInArea]
- `cursedMiscItem.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_Misc.lua:cursedMiscItem.onUse]
- `theCursedMiscAction.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_Misc.lua:theCursedMiscAction.onUse]
- `Action()` assigned to `cursedMiscItem` [actions_Misc.lua:cursedMiscItem]
- `Action()` assigned to `theCursedMiscAction` [actions_Misc.lua:theCursedMiscAction]
- `Action()` registration [actions_Misc.lua:Action]
- `theCursedOintment.onUse(player, item, frompos, item2, topos)` [actions_Ointment.lua:theCursedOintment.onUse]
- `Action()` assigned to `theCursedOintment` [actions_Ointment.lua:theCursedOintment]
- `Action()` registration [actions_Ointment.lua:Action]
- `isInArea(pos, fromPos, toPos)` [movements_StepIn_CursedCrystal.lua:isInArea]
- `StepInCursedCrystal.onStepIn(creature, item, position, fromPosition)` [movements_StepIn_CursedCrystal.lua:StepInCursedCrystal.onStepIn]
- `MoveEvent()` assigned to `StepInCursedCrystal` [movements_StepIn_CursedCrystal.lua:StepInCursedCrystal]
- `MoveEvent()` registration [movements_StepIn_CursedCrystal.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_MedusaOil.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_MedusaOil.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_MedusaOil.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_Misc.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_Misc.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_Ointment.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_Ointment.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_StepIn_CursedCrystal.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_StepIn_CursedCrystal.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_MedusaOil.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_MedusaOil.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_MedusaOil.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_MedusaOil.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_Misc.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_Misc.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_Misc.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_Misc.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_Misc.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_Ointment.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_Ointment.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_Ointment.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
