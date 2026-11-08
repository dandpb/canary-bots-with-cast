# The Order Of Lion

## Overview
Component package under `scripts/quests/the_order_of_lion` containing 5 files (`action-bounac_entrance.lua`..`moveevent-drume_entrance.lua`).

## Interface
- `bounacEntrance.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-bounac_entrance.lua:bounacEntrance.onUse]
- `Action()` assigned to `bounacEntrance` [action-bounac_entrance.lua:bounacEntrance]
- `Action()` registration [action-bounac_entrance.lua:Action]
- `clearRoomDrume(centerPosition, rangeX, rangeY, resetGlobalStorage)` [action-drume.lua:clearRoomDrume]
- `drumeAction.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-drume.lua:drumeAction.onUse]
- `Action()` assigned to `drumeAction` [action-drume.lua:drumeAction]
- `Action()` registration [action-drume.lua:Action]
- `elevatorBounacAction.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action-elevator.lua:elevatorBounacAction.onUse]
- `elevatorBounacMoveEvent.onStepIn(creature, item, position, fromPosition)` [action-elevator.lua:elevatorBounacMoveEvent.onStepIn]
- `Action()` assigned to `elevatorBounacAction` [action-elevator.lua:elevatorBounacAction]
- `Action()` registration [action-elevator.lua:Action]
- `MoveEvent()` assigned to `elevatorBounacMoveEvent` [action-elevator.lua:elevatorBounacMoveEvent]
- `MoveEvent()` registration [action-elevator.lua:MoveEvent]
- `lionCommanderDeath.onPrepareDeath(creature)` [creatureevent-commander_kills.lua:lionCommanderDeath.onPrepareDeath]
- `usurperCommanderDeath.onPrepareDeath(creature)` [creatureevent-commander_kills.lua:usurperCommanderDeath.onPrepareDeath]
- `kesarHealthChange.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)` [creatureevent-commander_kills.lua:kesarHealthChange.onHealthChange]
- `CreatureEvent("LionCommanderDeath")` assigned to `lionCommanderDeath` [creatureevent-commander_kills.lua:lionCommanderDeath]
- `CreatureEvent("UsurperCommanderDeath")` assigned to `usurperCommanderDeath` [creatureevent-commander_kills.lua:usurperCommanderDeath]
- `CreatureEvent("KesarImmortal")` assigned to `kesarHealthChange` [creatureevent-commander_kills.lua:kesarHealthChange]
- `CreatureEvent("LionCommanderDeath")` registration [creatureevent-commander_kills.lua:CreatureEvent]
- `CreatureEvent("UsurperCommanderDeath")` registration [creatureevent-commander_kills.lua:CreatureEvent]
- `CreatureEvent("KesarImmortal")` registration [creatureevent-commander_kills.lua:CreatureEvent]
- `drumeEntrance.onStepIn(creature, item, position, fromPosition)` [moveevent-drume_entrance.lua:drumeEntrance.onStepIn]
- `MoveEvent()` assigned to `drumeEntrance` [moveevent-drume_entrance.lua:drumeEntrance]
- `MoveEvent()` registration [moveevent-drume_entrance.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action-drume.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [action-drume.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action-drume.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [action-elevator.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creatureevent-commander_kills.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creatureevent-commander_kills.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [moveevent-drume_entrance.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-bounac_entrance.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [action-bounac_entrance.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-drume.lua:register]
- Mutates player or global storage state via `setStorageValue` [action-drume.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [action-drume.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [action-drume.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action-drume.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [action-drume.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action-elevator.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [action-elevator.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creatureevent-commander_kills.lua:register]
- Mutates player or global storage state via `setStorageValue` [creatureevent-commander_kills.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
