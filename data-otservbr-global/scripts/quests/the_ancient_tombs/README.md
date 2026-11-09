# The Ancient Tombs

## Overview
Component package under `scripts/quests/the_ancient_tombs` containing 23 files (`action_morguthis_wall.lua`..`movements_tomb_teleport.lua`).

## Interface
- `morguthisWall.onUse(player, item, fromPosition, target, toPosition)` [action_morguthis_wall.lua:morguthisWall.onUse]
- `Action()` assigned to `morguthisWall` [action_morguthis_wall.lua:morguthisWall]
- `Action()` registration [action_morguthis_wall.lua:Action]
- `resetScript(position, storage, configEntry, playerId)` [actions_active_teleport_switches.lua:resetScript]
- `theAncientActiveTeleport.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_active_teleport_switches.lua:theAncientActiveTeleport.onUse]
- `Action()` assigned to `theAncientActiveTeleport` [actions_active_teleport_switches.lua:theAncientActiveTeleport]
- `Action()` registration [actions_active_teleport_switches.lua:Action]
- `hasCompletedPreviousStep(player, currentStep)` [actions_dipthrah_signs_doors.lua:hasCompletedPreviousStep]
- `actions_dipthrah_signs_doors.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_dipthrah_signs_doors.lua:actions_dipthrah_signs_doors.onUse]
- `Action()` assigned to `actions_dipthrah_signs_doors` [actions_dipthrah_signs_doors.lua:actions_dipthrah_signs_doors]
- `Action()` registration [actions_dipthrah_signs_doors.lua:Action]
- `revertCarrotAndLever(position, carrotPosition)` [actions_oasis_lever_door.lua:revertCarrotAndLever]
- `theAncientOasisLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_oasis_lever_door.lua:theAncientOasisLever.onUse]
- `Action()` assigned to `theAncientOasisLever` [actions_oasis_lever_door.lua:theAncientOasisLever]
- `Action()` registration [actions_oasis_lever_door.lua:Action]
- `theAncientRuinsInstru.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ruins_instruments.lua:theAncientRuinsInstru.onUse]
- `Action()` assigned to `theAncientRuinsInstru` [actions_ruins_instruments.lua:theAncientRuinsInstru]
- `Action()` registration [actions_ruins_instruments.lua:Action]
- `tombCoalBasin.onAddItem(moveitem, tileitem, position)` [movements_all_teleports_tombs_coal_basin.lua:tombCoalBasin.onAddItem]
- `MoveEvent()` assigned to `tombCoalBasin` [movements_all_teleports_tombs_coal_basin.lua:tombCoalBasin]
- `MoveEvent()` registration [movements_all_teleports_tombs_coal_basin.lua:MoveEvent]
- `craftHelmet.onAddItem(moveitem, tileitem, position)` [movements_craft_helmet.lua:craftHelmet.onAddItem]
- `MoveEvent()` assigned to `craftHelmet` [movements_craft_helmet.lua:craftHelmet]
- `MoveEvent()` registration [movements_craft_helmet.lua:MoveEvent]
- `enterAshmunrahTeleport.onStepIn(creature, item, position, fromPosition)` [movements_enter_ashmunrah_teleport_switche_done.lua:enterAshmunrahTeleport.onStepIn]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action_morguthis_wall.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_active_teleport_switches.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_active_teleport_switches.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_dipthrah_signs_doors.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_oasis_lever_door.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ruins_instruments.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_all_teleports_tombs_coal_basin.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_all_teleports_tombs_coal_basin.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movements_all_teleports_tombs_coal_basin.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movements_craft_helmet.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_enter_ashmunrah_teleport_switche_done.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_enter_ashmunrah_teleport_switche_done.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_morguthis_wall.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [action_morguthis_wall.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [action_morguthis_wall.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_morguthis_wall.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_active_teleport_switches.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_active_teleport_switches.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_active_teleport_switches.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_active_teleport_switches.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_dipthrah_signs_doors.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_dipthrah_signs_doors.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_oasis_lever_door.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_oasis_lever_door.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
