# Assassin Outfit

## Overview
Component package under `scripts/quests/assassin_outfit` containing 1 files (`movements_erayo_house.lua`..`movements_erayo_house.lua`).

## Interface
- `erayoHouse.onStepIn(creature, item, position, fromPosition)` [movements_erayo_house.lua:erayoHouse.onStepIn]
- `MoveEvent()` assigned to `erayoHouse` [movements_erayo_house.lua:erayoHouse]
- `MoveEvent()` registration [movements_erayo_house.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_erayo_house.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_erayo_house.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_erayo_house.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
