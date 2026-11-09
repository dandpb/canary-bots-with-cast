# Blue Valley

## Overview
Component package under `scripts/blue_valley` containing 1 files (`monk_npcs_step_in.lua`..`monk_npcs_step_in.lua`).

## Interface
- `shouldSayMessage(pos, fromPos)` [monk_npcs_step_in.lua:shouldSayMessage]
- `monkGate.onStepIn(creature, item, position, fromPosition)` [monk_npcs_step_in.lua:monkGate.onStepIn]
- `MoveEvent()` assigned to `monkGate` [monk_npcs_step_in.lua:monkGate]
- `MoveEvent()` registration [monk_npcs_step_in.lua:MoveEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [monk_npcs_step_in.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [monk_npcs_step_in.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [monk_npcs_step_in.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
