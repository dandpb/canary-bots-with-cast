# The Djinn War Quest

## Overview
Component package under `scripts/quests/the_djinn_war_quest` containing 1 files (`action_water_fountain.lua`..`action_water_fountain.lua`).

## Interface
- `action_water_fountain.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_water_fountain.lua:action_water_fountain.onUse]
- `Action()` assigned to `action_water_fountain` [action_water_fountain.lua:action_water_fountain]
- `Action()` registration [action_water_fountain.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_water_fountain.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_water_fountain.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_water_fountain.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [action_water_fountain.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
