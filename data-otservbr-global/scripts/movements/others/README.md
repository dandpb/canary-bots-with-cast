# Others

## Overview
Component package under `scripts/movements/others` containing 5 files (`dawnport_tiles.lua`..`walkback.lua`).

## Interface
- `chestRoomTile.onStepIn(creature, item, position, fromPosition)` [dawnport_tiles.lua:chestRoomTile.onStepIn]
- `templeStairs.onStepIn(creature, item, position, fromPosition)` [dawnport_tiles.lua:templeStairs.onStepIn]
- `tutorialTile.onStepIn(creature, item, position, fromPosition)` [dawnport_tiles.lua:tutorialTile.onStepIn]
- `tutorialTile1.onStepIn(creature, item, position, fromPosition)` [dawnport_tiles.lua:tutorialTile1.onStepIn]
- `tutorialTile2.onStepIn(creature, item, position, fromPosition)` [dawnport_tiles.lua:tutorialTile2.onStepIn]
- `tutorialTile3.onStepIn(creature, item, position, fromPosition)` [dawnport_tiles.lua:tutorialTile3.onStepIn]
- `tutorialTile4.onStepIn(creature, item, position, fromPosition)` [dawnport_tiles.lua:tutorialTile4.onStepIn]
- `cureTile.onStepIn(creature, item, position, fromPosition)` [dawnport_tiles.lua:cureTile.onStepIn]
- `MoveEvent()` assigned to `chestRoomTile` [dawnport_tiles.lua:chestRoomTile]
- `MoveEvent()` assigned to `templeStairs` [dawnport_tiles.lua:templeStairs]
- `MoveEvent()` assigned to `tutorialTile` [dawnport_tiles.lua:tutorialTile]
- `MoveEvent()` assigned to `tutorialTile1` [dawnport_tiles.lua:tutorialTile1]
- `MoveEvent()` assigned to `tutorialTile2` [dawnport_tiles.lua:tutorialTile2]
- `MoveEvent()` assigned to `tutorialTile3` [dawnport_tiles.lua:tutorialTile3]
- `MoveEvent()` assigned to `tutorialTile4` [dawnport_tiles.lua:tutorialTile4]
- `MoveEvent()` assigned to `cureTile` [dawnport_tiles.lua:cureTile]
- `MoveEvent()` registration [dawnport_tiles.lua:MoveEvent]
- `addFirstItems(player)` [dawnport_vocation_trial.lua:addFirstItems]
- `tileStep(player, trial)` [dawnport_vocation_trial.lua:tileStep]
- `removeItems(player)` [dawnport_vocation_trial.lua:removeItems]
- `addItems(player, items)` [dawnport_vocation_trial.lua:addItems]
- `setOutfit(player, outfit)` [dawnport_vocation_trial.lua:setOutfit]
- `dawnportVocationTrial.onStepIn(creature, item, position, fromPosition)` [dawnport_vocation_trial.lua:dawnportVocationTrial.onStepIn]
- `MoveEvent()` assigned to `dawnportVocationTrial` [dawnport_vocation_trial.lua:dawnportVocationTrial]
- `MoveEvent()` registration [dawnport_vocation_trial.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [dawnport_tiles.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [dawnport_tiles.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [dawnport_vocation_trial.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [dawnport_vocation_trial.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [remove-create_item.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [remove-create_item.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [teleport.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [walkback.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [dawnport_tiles.lua:register]
- Mutates player or global storage state via `setStorageValue` [dawnport_tiles.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [dawnport_tiles.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [dawnport_vocation_trial.lua:register]
- Mutates player or global storage state via `setStorageValue` [dawnport_vocation_trial.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [dawnport_vocation_trial.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [dawnport_vocation_trial.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [remove-create_item.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [remove-create_item.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [remove-create_item.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [teleport.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [teleport.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
