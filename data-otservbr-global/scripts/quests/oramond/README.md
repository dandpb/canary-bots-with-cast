# Oramond

## Overview
Provides 1 direct files (`actions_glooth_fairy_lever.lua`..`actions_glooth_fairy_lever.lua`) and 4 subdirectories under `scripts/quests/oramond`.

## Interface
- `clearMonstersAndTeleportPlayers()` [actions_glooth_fairy_lever.lua:clearMonstersAndTeleportPlayers]
- `gloothFairyLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_glooth_fairy_lever.lua:gloothFairyLever.onUse]
- `Action()` assigned to `gloothFairyLever` [actions_glooth_fairy_lever.lua:gloothFairyLever]
- `Action()` registration [actions_glooth_fairy_lever.lua:Action]
- [probing](./probing/README.md) - Component package under `scripts/quests/oramond/probing` containing 1 files (`actions_mono_detector_strange_probing_device.lua`..`actions_mono_detector_strange_probing_device.lua`).
- [the_ancient_sewers](./the_ancient_sewers/README.md) - Component package under `scripts/quests/oramond/the_ancient_sewers` containing 1 files (`actions_the_ancient_sewers.lua`..`actions_the_ancient_sewers.lua`).
- [the_powder_of_the_stars](./the_powder_of_the_stars/README.md) - Component package under `scripts/quests/oramond/the_powder_of_the_stars` containing 1 files (`actions_blue_pollen.lua`..`actions_blue_pollen.lua`).
- [to_take_roots](./to_take_roots/README.md) - Component package under `scripts/quests/oramond/to_take_roots` containing 1 files (`actions_to_take_roots.lua`..`actions_to_take_roots.lua`).

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_glooth_fairy_lever.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_glooth_fairy_lever.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_glooth_fairy_lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_glooth_fairy_lever.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_glooth_fairy_lever.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_glooth_fairy_lever.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_glooth_fairy_lever.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_glooth_fairy_lever.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_glooth_fairy_lever.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
