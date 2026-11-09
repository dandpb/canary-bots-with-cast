# The Spike Tasks

## Overview
Component package under `scripts/quests/the_spike_tasks` containing 2 files (`movements_geomantic_charges.lua`..`movements_spike_teleport.lua`).

## Interface
- `geomanticCharges.onStepIn(creature, item, position, fromPosition)` [movements_geomantic_charges.lua:geomanticCharges.onStepIn]
- `MoveEvent()` assigned to `geomanticCharges` [movements_geomantic_charges.lua:geomanticCharges]
- `MoveEvent()` registration [movements_geomantic_charges.lua:MoveEvent]
- `spikeTeleport.onStepIn(creature, item, position, fromPosition)` [movements_spike_teleport.lua:spikeTeleport.onStepIn]
- `MoveEvent()` assigned to `spikeTeleport` [movements_spike_teleport.lua:spikeTeleport]
- `MoveEvent()` registration [movements_spike_teleport.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_geomantic_charges.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_geomantic_charges.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_spike_teleport.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_geomantic_charges.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_geomantic_charges.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_geomantic_charges.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_spike_teleport.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_spike_teleport.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
