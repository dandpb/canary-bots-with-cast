# The Travelling Trader

## Overview
Component package under `scripts/quests/the_travelling_trader` containing 1 files (`actions_outlaw_camp_door.lua`..`actions_outlaw_camp_door.lua`).

## Interface
- `outlawCamp.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_outlaw_camp_door.lua:outlawCamp.onUse]
- `Action()` assigned to `outlawCamp` [actions_outlaw_camp_door.lua:outlawCamp]
- `Action()` registration [actions_outlaw_camp_door.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_outlaw_camp_door.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_outlaw_camp_door.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_outlaw_camp_door.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_outlaw_camp_door.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
