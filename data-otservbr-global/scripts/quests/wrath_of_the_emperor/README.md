# Wrath Of The Emperor

## Overview
Component package under `scripts/quests/wrath_of_the_emperor` containing 22 files (`actions_mission01_crate.lua`..`movements_teleports_access.lua`).

## Interface
- `wrathEmperorMiss1Crate.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission01_crate.lua:wrathEmperorMiss1Crate.onUse]
- `Action()` assigned to `wrathEmperorMiss1Crate` [actions_mission01_crate.lua:wrathEmperorMiss1Crate]
- `Action()` registration [actions_mission01_crate.lua:Action]
- `transformLamp(position, itemId, transformId)` [actions_mission01_lights.lua:transformLamp]
- `wrathEmperorMiss1Light.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission01_lights.lua:wrathEmperorMiss1Light.onUse]
- `Action()` assigned to `wrathEmperorMiss1Light` [actions_mission01_lights.lua:wrathEmperorMiss1Light]
- `Action()` registration [actions_mission01_lights.lua:Action]
- `revertWater(position)` [actions_mission02_firstcontact_repair_teleport.lua:revertWater]
- `wrathEmperorMiss2FirstContact.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission02_firstcontact_repair_teleport.lua:wrathEmperorMiss2FirstContact.onUse]
- `Action()` assigned to `wrathEmperorMiss2FirstContact` [actions_mission02_firstcontact_repair_teleport.lua:wrathEmperorMiss2FirstContact]
- `Action()` registration [actions_mission02_firstcontact_repair_teleport.lua:Action]
- `revertKeeperstorage()` [actions_mission03_the_keeper.lua:revertKeeperstorage]
- `wrathEmperorMiss3Keeper.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission03_the_keeper.lua:wrathEmperorMiss3Keeper.onUse]
- `Action()` assigned to `wrathEmperorMiss3Keeper` [actions_mission03_the_keeper.lua:wrathEmperorMiss3Keeper]
- `Action()` registration [actions_mission03_the_keeper.lua:Action]
- `wrathEmperorMiss4Sacrament.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission04_sacrament_of_the_snake_sceptre.lua:wrathEmperorMiss4Sacrament.onUse]
- `Action()` assigned to `wrathEmperorMiss4Sacrament` [actions_mission04_sacrament_of_the_snake_sceptre.lua:wrathEmperorMiss4Sacrament]
- `Action()` registration [actions_mission04_sacrament_of_the_snake_sceptre.lua:Action]
- `doors.onUse(player, target)` [actions_mission08_doors.lua:doors.onUse]
- `Action()` assigned to `doors` [actions_mission08_doors.lua:doors]
- `Action()` registration [actions_mission08_doors.lua:Action]
- `wrathEmperorMiss8Uninvited.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission08_uninvited_guests_lever.lua:wrathEmperorMiss8Uninvited.onUse]
- `Action()` assigned to `wrathEmperorMiss8Uninvited` [actions_mission08_uninvited_guests_lever.lua:wrathEmperorMiss8Uninvited]
- `Action()` registration [actions_mission08_uninvited_guests_lever.lua:Action]
- `wrathEmperorMiss9Sleeping.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission09_the_sleeping_dragon_mixture.lua:wrathEmperorMiss9Sleeping.onUse]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission01_crate.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission01_lights.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_mission01_lights.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission02_firstcontact_repair_teleport.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_mission02_firstcontact_repair_teleport.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission03_the_keeper.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission04_sacrament_of_the_snake_sceptre.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_mission08_uninvited_guests_lever.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_mission08_uninvited_guests_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission09_the_sleeping_dragon_mixture.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission10_a_message_of_freedom_sceptre.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission11_payback_time_lever.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission01_crate.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission01_lights.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_mission01_lights.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_mission01_lights.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mission01_lights.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_mission01_lights.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission02_firstcontact_repair_teleport.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_mission02_firstcontact_repair_teleport.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mission02_firstcontact_repair_teleport.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_mission02_firstcontact_repair_teleport.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission03_the_keeper.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_mission03_the_keeper.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
