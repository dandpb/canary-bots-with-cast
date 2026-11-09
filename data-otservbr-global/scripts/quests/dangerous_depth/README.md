# Dangerous Depth

## Overview
Component package under `scripts/quests/dangerous_depth` containing 24 files (`actions_crude_lava_pump.lua`..`movements_warzone_entrance.lua`).

## Interface
- `dangerousDepthPump.onUse(player, item)` [actions_crude_lava_pump.lua:dangerousDepthPump.onUse]
- `Action()` assigned to `dangerousDepthPump` [actions_crude_lava_pump.lua:dangerousDepthPump]
- `Action()` registration [actions_crude_lava_pump.lua:Action]
- `explosion(item)` [actions_crude_lava_pump_achievements.lua:explosion]
- `dangerousDepthAchievements.onUse(player, item)` [actions_crude_lava_pump_achievements.lua:dangerousDepthAchievements.onUse]
- `Action()` assigned to `dangerousDepthAchievements` [actions_crude_lava_pump_achievements.lua:dangerousDepthAchievements]
- `Action()` registration [actions_crude_lava_pump_achievements.lua:Action]
- `dangerousDepthChart.onUse(player, item, isHotkey)` [actions_gnome_chart.lua:dangerousDepthChart.onUse]
- `Action()` assigned to `dangerousDepthChart` [actions_gnome_chart.lua:dangerousDepthChart]
- `Action()` registration [actions_gnome_chart.lua:Action]
- `dangerousDepthItems.onUse(player, item)` [actions_gnome_items.lua:dangerousDepthItems.onUse]
- `Action()` assigned to `dangerousDepthItems` [actions_gnome_items.lua:dangerousDepthItems]
- `Action()` registration [actions_gnome_items.lua:Action]
- `dangerousDepthTrignometre.onUse(player, item, isHotkey)` [actions_gnome_trignometre.lua:dangerousDepthTrignometre.onUse]
- `Action()` assigned to `dangerousDepthTrignometre` [actions_gnome_trignometre.lua:dangerousDepthTrignometre]
- `Action()` registration [actions_gnome_trignometre.lua:Action]
- `dangerousDepthChest.onUse(player, item)` [actions_gnomish_chest.lua:dangerousDepthChest.onUse]
- `Action()` assigned to `dangerousDepthChest` [actions_gnomish_chest.lua:dangerousDepthChest]
- `Action()` registration [actions_gnomish_chest.lua:Action]
- `dangerousDepthPesticide.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_gnomish_pesticide.lua:dangerousDepthPesticide.onUse]
- `Action()` assigned to `dangerousDepthPesticide` [actions_gnomish_pesticide.lua:dangerousDepthPesticide]
- `Action()` registration [actions_gnomish_pesticide.lua:Action]
- `checkPos(item)` [actions_lever_barrel.lua:checkPos]
- `explode(item)` [actions_lever_barrel.lua:explode]
- `dangerousDepthLever.onUse(player, item)` [actions_lever_barrel.lua:dangerousDepthLever.onUse]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_crude_lava_pump.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_crude_lava_pump.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_crude_lava_pump_achievements.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_crude_lava_pump_achievements.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_gnome_chart.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_gnome_items.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_gnome_trignometre.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_gnomish_chest.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_gnomish_pesticide.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lever_barrel.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_lever_barrel.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_using_crystals.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_crude_lava_pump.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_crude_lava_pump.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_crude_lava_pump.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_crude_lava_pump.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_crude_lava_pump_achievements.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_crude_lava_pump_achievements.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_gnome_chart.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_gnome_chart.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_gnome_items.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_gnome_items.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_gnome_items.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_gnome_trignometre.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
