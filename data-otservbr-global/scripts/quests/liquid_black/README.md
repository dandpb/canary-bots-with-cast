# Liquid Black

## Overview
Component package under `scripts/quests/liquid_black` containing 7 files (`actions_chairteleport.lua`..`movements_shortcut.lua`).

## Interface
- `chairteleport.onUse(player, item, frompos, item2, topos)` [actions_chairteleport.lua:chairteleport.onUse]
- `Action()` assigned to `chairteleport` [actions_chairteleport.lua:chairteleport]
- `Action()` registration [actions_chairteleport.lua:Action]
- `notescoordinates.onUse(player, item, frompos, item2, topos)` [actions_notescoordinates.lua:notescoordinates.onUse]
- `Action()` assigned to `notescoordinates` [actions_notescoordinates.lua:notescoordinates]
- `Action()` registration [actions_notescoordinates.lua:Action]
- `seashellKey.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_seashell_key.lua:seashellKey.onUse]
- `Action()` assigned to `seashellKey` [actions_seashell_key.lua:seashellKey]
- `Action()` registration [actions_seashell_key.lua:Action]
- `deeplingBosses.onDeath(creature)` [creaturescripts_deepling_boss_kill.lua:deeplingBosses.onDeath]
- `CreatureEvent("DeeplingBossDeath")` assigned to `deeplingBosses` [creaturescripts_deepling_boss_kill.lua:deeplingBosses]
- `CreatureEvent("DeeplingBossDeath")` registration [creaturescripts_deepling_boss_kill.lua:CreatureEvent]
- `ladder.onStepIn(creature, item, toPosition, fromPosition)` [movements_ladder.lua:ladder.onStepIn]
- `MoveEvent()` assigned to `ladder` [movements_ladder.lua:ladder]
- `MoveEvent()` registration [movements_ladder.lua:MoveEvent]
- `quickAccess.onStepIn(creature, item, toPosition, fromPosition)` [movements_quick_access.lua:quickAccess.onStepIn]
- `MoveEvent()` assigned to `quickAccess` [movements_quick_access.lua:quickAccess]
- `MoveEvent()` registration [movements_quick_access.lua:MoveEvent]
- `shortcut.onStepIn(creature, item, toPosition, fromPosition)` [movements_shortcut.lua:shortcut.onStepIn]
- `MoveEvent()` assigned to `shortcut` [movements_shortcut.lua:shortcut]
- `MoveEvent()` registration [movements_shortcut.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_chairteleport.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_notescoordinates.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_deepling_boss_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_ladder.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_ladder.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_quick_access.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_quick_access.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_shortcut.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_shortcut.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_chairteleport.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_chairteleport.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_chairteleport.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_notescoordinates.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_notescoordinates.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_notescoordinates.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_seashell_key.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_seashell_key.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_deepling_boss_kill.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_deepling_boss_kill.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_ladder.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_ladder.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
