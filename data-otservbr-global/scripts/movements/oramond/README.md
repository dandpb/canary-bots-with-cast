# Oramond

## Overview
Component package under `scripts/movements/oramond` containing 6 files (`oramond_entrance.lua`..`voting_oramond.lua`).

## Interface
- `oramondEntrance.onStepIn(creature, item, position, fromPosition)` [oramond_entrance.lua:oramondEntrance.onStepIn]
- `MoveEvent()` assigned to `oramondEntrance` [oramond_entrance.lua:oramondEntrance]
- `MoveEvent()` registration [oramond_entrance.lua:MoveEvent]
- `oramondMovements.onStepIn(creature, item, position, fromPosition)` [oramond_movements.lua:oramondMovements.onStepIn]
- `MoveEvent()` assigned to `oramondMovements` [oramond_movements.lua:oramondMovements]
- `MoveEvent()` registration [oramond_movements.lua:MoveEvent]
- `oramondTeleport.onStepIn(creature, item, position, fromPosition)` [oramond_teleport.lua:oramondTeleport.onStepIn]
- `MoveEvent()` assigned to `oramondTeleport` [oramond_teleport.lua:oramondTeleport]
- `MoveEvent()` registration [oramond_teleport.lua:MoveEvent]
- `oramondSeacrest.onStepIn(creature, item, position, fromPosition)` [seacrest.lua:oramondSeacrest.onStepIn]
- `MoveEvent()` assigned to `oramondSeacrest` [seacrest.lua:oramondSeacrest]
- `MoveEvent()` registration [seacrest.lua:MoveEvent]
- `oramondTeleports.onStepIn(creature, item, position, fromPosition)` [teleport.lua:oramondTeleports.onStepIn]
- `MoveEvent()` assigned to `oramondTeleports` [teleport.lua:oramondTeleports]
- `MoveEvent()` registration [teleport.lua:MoveEvent]
- `votingOramond.onStepIn(creature, item, position, fromPosition)` [voting_oramond.lua:votingOramond.onStepIn]
- `MoveEvent()` assigned to `votingOramond` [voting_oramond.lua:votingOramond]
- `MoveEvent()` registration [voting_oramond.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [oramond_entrance.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [oramond_movements.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [oramond_teleport.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [seacrest.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [teleport.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [voting_oramond.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [oramond_entrance.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [oramond_entrance.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [oramond_movements.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [oramond_movements.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [oramond_teleport.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [oramond_teleport.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [seacrest.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [seacrest.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [teleport.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [teleport.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [voting_oramond.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [voting_oramond.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
