# Deeplings Worldchange

## Overview
Component package under `scripts/quests/deeplings_worldchange` containing 8 files (`actions_boxramp.lua`..`movements_deepling_bosses.lua`).

## Interface
- `boxRamp.onUse(player, item, frompos, item2, topos)` [actions_boxramp.lua:boxRamp.onUse]
- `Action()` assigned to `boxRamp` [actions_boxramp.lua:boxRamp]
- `Action()` registration [actions_boxramp.lua:Action]
- `crystaldeepling.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_coral.lua:crystaldeepling.onUse]
- `Action()` assigned to `crystaldeepling` [actions_coral.lua:crystaldeepling]
- `Action()` registration [actions_coral.lua:Action]
- `crystaldeepling.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_crystal.lua:crystaldeepling.onUse]
- `Action()` assigned to `crystaldeepling` [actions_crystal.lua:crystaldeepling]
- `Action()` registration [actions_crystal.lua:Action]
- `crystalvortex.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_crystalvortex.lua:crystalvortex.onUse]
- `Action()` assigned to `crystalvortex` [actions_crystalvortex.lua:crystalvortex]
- `Action()` registration [actions_crystalvortex.lua:Action]
- `goldenAnchorTeleport.onUse(creature, item, fromPosition, target, toPosition, isHotkey)` [actions_golden_anchor.lua:goldenAnchorTeleport.onUse]
- `Action()` assigned to `goldenAnchorTeleport` [actions_golden_anchor.lua:goldenAnchorTeleport]
- `Action()` registration [actions_golden_anchor.lua:Action]
- `questFirst.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_questfirst.lua:questFirst.onUse]
- `Action()` assigned to `questFirst` [actions_questfirst.lua:questFirst]
- `Action()` registration [actions_questfirst.lua:Action]
- `statuegod.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_statue.lua:statuegod.onUse]
- `Action()` assigned to `statuegod` [actions_statue.lua:statuegod]
- `Action()` registration [actions_statue.lua:Action]
- `deeplingBosses.onStepIn(creature, item, position, fromPosition)` [movements_deepling_bosses.lua:deeplingBosses.onStepIn]
- `MoveEvent()` assigned to `deeplingBosses` [movements_deepling_bosses.lua:deeplingBosses]
- `MoveEvent()` registration [movements_deepling_bosses.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_boxramp.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_coral.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_crystal.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_crystalvortex.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_golden_anchor.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_questfirst.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_statue.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_deepling_bosses.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_deepling_bosses.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_boxramp.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_boxramp.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_boxramp.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_coral.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_coral.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_coral.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_coral.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_crystal.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_crystal.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_crystal.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_crystal.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_crystalvortex.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
