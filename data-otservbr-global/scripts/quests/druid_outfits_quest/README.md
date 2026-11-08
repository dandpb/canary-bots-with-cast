# Druid Outfits Quest

## Overview
Component package under `scripts/quests/druid_outfits_quest` containing 2 files (`actions_ceirons_waterskin.lua`..`globalevents_druid_outfits_blooming_griffinclaw.lua`).

## Interface
- `actions_ceirons_waterskin.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ceirons_waterskin.lua:actions_ceirons_waterskin.onUse]
- `Action()` assigned to `actions_ceirons_waterskin` [actions_ceirons_waterskin.lua:actions_ceirons_waterskin]
- `Action()` registration [actions_ceirons_waterskin.lua:Action]
- `decayFlower(tile)` [globalevents_druid_outfits_blooming_griffinclaw.lua:decayFlower]
- `bloom()` [globalevents_druid_outfits_blooming_griffinclaw.lua:bloom]
- `druidOutfit.onStartup()` [globalevents_druid_outfits_blooming_griffinclaw.lua:druidOutfit.onStartup]
- `GlobalEvent("blooming griffinclaw")` assigned to `druidOutfit` [globalevents_druid_outfits_blooming_griffinclaw.lua:druidOutfit]
- `GlobalEvent("blooming griffinclaw")` registration [globalevents_druid_outfits_blooming_griffinclaw.lua:GlobalEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ceirons_waterskin.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [globalevents_druid_outfits_blooming_griffinclaw.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ceirons_waterskin.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_ceirons_waterskin.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_ceirons_waterskin.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [globalevents_druid_outfits_blooming_griffinclaw.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [globalevents_druid_outfits_blooming_griffinclaw.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [globalevents_druid_outfits_blooming_griffinclaw.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
