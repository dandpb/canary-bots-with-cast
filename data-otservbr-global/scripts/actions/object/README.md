# Object

## Overview
Component package under `scripts/actions/object` containing 7 files (`dancingfairy.lua`..`wz789_entrance.lua`).

## Interface
- `dancingfairy.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [dancingfairy.lua:dancingfairy.onUse]
- `Action()` assigned to `dancingfairy` [dancingfairy.lua:dancingfairy]
- `Action()` registration [dancingfairy.lua:Action]
- `moveEvent.onStepIn(creature, item, position, fromPosition)` [deathlings_entrance.lua:moveEvent.onStepIn]
- `MoveEvent()` assigned to `moveEvent` [deathlings_entrance.lua:moveEvent]
- `MoveEvent()` registration [deathlings_entrance.lua:MoveEvent]
- `goldenOutfitDisplay.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [golden_outfit_display.lua:goldenOutfitDisplay.onUse]
- `Action()` assigned to `goldenOutfitDisplay` [golden_outfit_display.lua:goldenOutfitDisplay]
- `Action()` registration [golden_outfit_display.lua:Action]
- `imbuement.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [imbuement_shrine.lua:imbuement.onUse]
- `Action()` assigned to `imbuement` [imbuement_shrine.lua:imbuement]
- `Action()` registration [imbuement_shrine.lua:Action]
- `moonlightCrystals.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [moonlight_crystals.lua:moonlightCrystals.onUse]
- `Action()` assigned to `moonlightCrystals` [moonlight_crystals.lua:moonlightCrystals]
- `Action()` registration [moonlight_crystals.lua:Action]
- `cobraBastion.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [rope_down.lua:cobraBastion.onUse]
- `oskayaat.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [rope_down.lua:oskayaat.onUse]
- `Action()` assigned to `cobraBastion` [rope_down.lua:cobraBastion]
- `Action()` assigned to `oskayaat` [rope_down.lua:oskayaat]
- `Action()` registration [rope_down.lua:Action]
- `moveEvent.onStepIn(creature, item, position, fromPosition)` [wz789_entrance.lua:moveEvent.onStepIn]
- `MoveEvent()` assigned to `moveEvent` [wz789_entrance.lua:moveEvent]
- `MoveEvent()` registration [wz789_entrance.lua:MoveEvent]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [dancingfairy.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [deathlings_entrance.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [golden_outfit_display.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [imbuement_shrine.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [moonlight_crystals.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [wz789_entrance.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [dancingfairy.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [dancingfairy.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [dancingfairy.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [deathlings_entrance.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [deathlings_entrance.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [golden_outfit_display.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [golden_outfit_display.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [imbuement_shrine.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [moonlight_crystals.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [moonlight_crystals.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [rope_down.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [rope_down.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
