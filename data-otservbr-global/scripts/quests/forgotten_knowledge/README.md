# Forgotten Knowledge

## Overview
Component package under `scripts/quests/forgotten_knowledge` containing 43 files (`actions_bird_cage.lua`..`movements_teleport_tree.lua`).

## Interface
- Defines 43 script/configuration files (`actions_bird_cage.lua` through `movements_teleport_tree.lua`) [actions_bird_cage.lua]
- `forgottenKnowledgeBird.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bird_cage.lua:forgottenKnowledgeBird.onUse]
- `Action()` assigned to `forgottenKnowledgeBird` [actions_bird_cage.lua:forgottenKnowledgeBird]
- `Action()` registration [actions_bird_cage.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_dragonking_zyrtarch.lua:lever]
- `BossLever(config)` registration [actions_dragonking_zyrtarch.lua:BossLever]
- `forgottenKnowledgeFount.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_fount.lua:forgottenKnowledgeFount.onUse]
- `Action()` assigned to `forgottenKnowledgeFount` [actions_fount.lua:forgottenKnowledgeFount]
- `Action()` registration [actions_fount.lua:Action]
- `leverMeltingFrozenHorror.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_frozen_horror.lua:leverMeltingFrozenHorror.onUse]
- `Action()` assigned to `leverMeltingFrozenHorror` [actions_frozen_horror.lua:leverMeltingFrozenHorror]
- `Action()` registration [actions_frozen_horror.lua:Action]
- `forgottenKnowledgeGirl.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_girl_picture.lua:forgottenKnowledgeGirl.onUse]
- `Action()` assigned to `forgottenKnowledgeGirl` [actions_girl_picture.lua:forgottenKnowledgeGirl]
- `Action()` registration [actions_girl_picture.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_lady_tenebris.lua:lever]
- `BossLever(config)` registration [actions_lady_tenebris.lua:BossLever]
- `forgottenKnowledgeLantern.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lantern.lua:forgottenKnowledgeLantern.onUse]
- `Action()` assigned to `forgottenKnowledgeLantern` [actions_lantern.lua:forgottenKnowledgeLantern]
- `Action()` registration [actions_lantern.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_lloyd.lua:lever]
- `BossLever(config)` registration [actions_lloyd.lua:BossLever]
- `forgottenKnowledgeLostTime.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lost_time.lua:forgottenKnowledgeLostTime.onUse]
- `Action()` assigned to `forgottenKnowledgeLostTime` [actions_lost_time.lua:forgottenKnowledgeLostTime]
- `Action()` registration [actions_lost_time.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_bird_cage.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_fount.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_frozen_horror.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_frozen_horror.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_frozen_horror.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_girl_picture.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lantern.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_old_desk.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_plant.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_plant.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_secret_wall.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_servants_mechanism.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bird_cage.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_bird_cage.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bird_cage.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_dragonking_zyrtarch.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_fount.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_fount.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_fount.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_frozen_horror.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_frozen_horror.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_frozen_horror.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_frozen_horror.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_frozen_horror.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
