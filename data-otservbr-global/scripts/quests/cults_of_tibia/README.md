# Cults Of Tibia

## Overview
Component package under `scripts/quests/cults_of_tibia` containing 42 files (`actions_analyser.lua`..`movements_teleport_from_essence_of_malice.lua`).

## Interface
- Defines 42 script/configuration files (`actions_analyser.lua` through `movements_teleport_from_essence_of_malice.lua`) [actions_analyser.lua]
- `cultsOfTibiaAnalyser.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_analyser.lua:cultsOfTibiaAnalyser.onUse]
- `Action()` assigned to `cultsOfTibiaAnalyser` [actions_analyser.lua:cultsOfTibiaAnalyser]
- `Action()` registration [actions_analyser.lua:Action]
- `spawnStolenSoul(t_time)` [actions_bosses_levers.lua:spawnStolenSoul]
- `spawnDarkSoul(area, t_time)` [actions_bosses_levers.lua:spawnDarkSoul]
- `transformMonster(itid, action, monster, frompos, topos, _temp)` [actions_bosses_levers.lua:transformMonster]
- `activateGeyser(player)` [actions_bosses_levers.lua:activateGeyser]
- `cultsOfTibiaLevers.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_bosses_levers.lua:cultsOfTibiaLevers.onUse]
- `createBeam1(fromPos, toPos, id, dir)` [actions_bosses_levers.lua:createBeam1]
- `Action()` assigned to `cultsOfTibiaLevers` [actions_bosses_levers.lua:cultsOfTibiaLevers]
- `Action()` registration [actions_bosses_levers.lua:Action]
- `cultsOfTibiaCounter.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_counter_agent.lua:cultsOfTibiaCounter.onUse]
- `Action()` assigned to `cultsOfTibiaCounter` [actions_counter_agent.lua:cultsOfTibiaCounter]
- `Action()` registration [actions_counter_agent.lua:Action]
- `cultsOfTibiaCrate.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_crate.lua:cultsOfTibiaCrate.onUse]
- `Action()` assigned to `cultsOfTibiaCrate` [actions_crate.lua:cultsOfTibiaCrate]
- `Action()` registration [actions_crate.lua:Action]
- `cultsOfTibiaCult.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_cult_symbol.lua:cultsOfTibiaCult.onUse]
- `Action()` assigned to `cultsOfTibiaCult` [actions_cult_symbol.lua:cultsOfTibiaCult]
- `Action()` registration [actions_cult_symbol.lua:Action]
- `cultsOfTibiaDocument.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_document.lua:cultsOfTibiaDocument.onUse]
- `Action()` assigned to `cultsOfTibiaDocument` [actions_document.lua:cultsOfTibiaDocument]
- `Action()` registration [actions_document.lua:Action]
- `cultsOfTibiaLastObject.onUse(player, item)` [actions_last_object.lua:cultsOfTibiaLastObject.onUse]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_analyser.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_bosses_levers.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_bosses_levers.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_counter_agent.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_crate.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_cult_symbol.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_document.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_last_object.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lever_mota.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_lever_mota.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_magnifier.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_magnifier.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_analyser.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_analyser.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bosses_levers.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_bosses_levers.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_bosses_levers.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_bosses_levers.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bosses_levers.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_bosses_levers.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_counter_agent.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_counter_agent.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_counter_agent.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_crate.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
