# Edron Rope

## Overview
Component package under `scripts/quests/edron_rope` containing 1 files (`movements_rope.lua`..`movements_rope.lua`).

## Interface
- `rope.onStepIn(creature, item, position, fromPosition)` [movements_rope.lua:rope.onStepIn]
- `MoveEvent()` assigned to `rope` [movements_rope.lua:rope]
- `MoveEvent()` registration [movements_rope.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_rope.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_rope.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_rope.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_rope.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
