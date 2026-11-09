# Heart Of Destruction

## Overview
Component package under `scripts/quests/heart_of_destruction` containing 39 files (`actions_anomaly.lua`..`movements_vortex_hunger.lua`).

## Interface
- Defines 39 script/configuration files (`actions_anomaly.lua` through `movements_vortex_hunger.lua`) [actions_anomaly.lua]
- `BossLever(config)` assigned to `lever` [actions_anomaly.lua:lever]
- `BossLever(config)` registration [actions_anomaly.lua:BossLever]
- `shuffleTable(t, count, ri, rj)` [actions_charges_lever.lua:shuffleTable]
- `doCheckArea()` [actions_charges_lever.lua:doCheckArea]
- `clearArea()` [actions_charges_lever.lua:clearArea]
- `teleportToCrackler()` [actions_charges_lever.lua:teleportToCrackler]
- `teleportToCharger()` [actions_charges_lever.lua:teleportToCharger]
- `heartDestructionCharges.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_charges_lever.lua:heartDestructionCharges.onUse]
- `Action()` assigned to `heartDestructionCharges` [actions_charges_lever.lua:heartDestructionCharges]
- `Action()` registration [actions_charges_lever.lua:Action]
- `doCheckArea()` [actions_cracklers_lever.lua:doCheckArea]
- `clearArea()` [actions_cracklers_lever.lua:clearArea]
- `createVortex()` [actions_cracklers_lever.lua:createVortex]
- `heartDestructionCracklers.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_cracklers_lever.lua:heartDestructionCracklers.onUse]
- `Action()` assigned to `heartDestructionCracklers` [actions_cracklers_lever.lua:heartDestructionCracklers]
- `Action()` registration [actions_cracklers_lever.lua:Action]
- `heartDestructionDevourer.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_devourer_access.lua:heartDestructionDevourer.onUse]
- `Action()` assigned to `heartDestructionDevourer` [actions_devourer_access.lua:heartDestructionDevourer]
- `Action()` registration [actions_devourer_access.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_eradicator.lua:lever]
- `BossLever(config)` registration [actions_eradicator.lua:BossLever]
- `sparkDevourerSpawn()` [actions_final_lever.lua:sparkDevourerSpawn]
- `doCheckArea()` [actions_final_lever.lua:doCheckArea]
- `changeArea()` [actions_final_lever.lua:changeArea]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_anomaly.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_charges_lever.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_charges_lever.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_cracklers_lever.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_cracklers_lever.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_eradicator.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_final_lever.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_final_lever.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_final_lever.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_foreshock.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_outburst.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_reward.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_anomaly.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_anomaly.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_anomaly.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_charges_lever.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_charges_lever.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_charges_lever.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_charges_lever.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_charges_lever.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_charges_lever.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_cracklers_lever.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_cracklers_lever.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_cracklers_lever.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
