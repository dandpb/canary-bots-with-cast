# The Way Of The Monk

## Overview
Component package under `scripts/quests/the_way_of_the_monk` containing 3 files (`blue_valley_teleport.lua`..`shrines_dawnport.lua`).

## Interface
- `performTeleport(player, teleportDestination, effectPos)` [blue_valley_teleport.lua:performTeleport]
- `BlueValleyTeleport.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [blue_valley_teleport.lua:BlueValleyTeleport.onUse]
- `Action()` assigned to `BlueValleyTeleport` [blue_valley_teleport.lua:BlueValleyTeleport]
- `Action()` registration [blue_valley_teleport.lua:Action]
- `parseRewards(player, rewardsTable)` [shrines.lua:parseRewards]
- `Shrines.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [shrines.lua:Shrines.onUse]
- `Action()` assigned to `Shrines` [shrines.lua:Shrines]
- `Action()` registration [shrines.lua:Action]
- Global symbol `TheWayOfTheMonkShrines` [shrines.lua:TheWayOfTheMonkShrines]
- `Shrines.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [shrines_dawnport.lua:Shrines.onUse]
- `Action()` assigned to `Shrines` [shrines_dawnport.lua:Shrines]
- `Action()` registration [shrines_dawnport.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [shrines.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [shrines_dawnport.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [blue_valley_teleport.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [blue_valley_teleport.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [shrines.lua:register]
- Mutates player or global storage state via `setStorageValue` [shrines.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [shrines.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [shrines.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [shrines_dawnport.lua:register]
- Mutates player or global storage state via `setStorageValue` [shrines_dawnport.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [shrines_dawnport.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [shrines_dawnport.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
