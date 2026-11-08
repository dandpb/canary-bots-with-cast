# Demon Oak

## Overview
Component package under `scripts/quests/demon_oak` containing 7 files (`actions_demon_oak.lua`..`movements_squares.lua`).

## Interface
- `getRandomSummonPosition()` [actions_demon_oak.lua:getRandomSummonPosition]
- `demonOak.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_demon_oak.lua:demonOak.onUse]
- `Action()` assigned to `demonOak` [actions_demon_oak.lua:demonOak]
- `Action()` registration [actions_demon_oak.lua:Action]
- `demonOakChest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_demon_oak_chest.lua:demonOakChest.onUse]
- `Action()` assigned to `demonOakChest` [actions_demon_oak_chest.lua:demonOakChest]
- `Action()` registration [actions_demon_oak_chest.lua:Action]
- `demonOakGrave.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_demon_oak_gravestone.lua:demonOakGrave.onUse]
- `Action()` assigned to `demonOakGrave` [actions_demon_oak_gravestone.lua:demonOakGrave]
- `Action()` registration [actions_demon_oak_gravestone.lua:Action]
- `demonOakVoices.onThink(interval, lastExecution)` [globalevents_demon_oak_voices.lua:demonOakVoices.onThink]
- `GlobalEvent("demon oak voices")` assigned to `demonOakVoices` [globalevents_demon_oak_voices.lua:demonOakVoices]
- `GlobalEvent("demon oak voices")` registration [globalevents_demon_oak_voices.lua:GlobalEvent]
- `areaDamage.onStepIn(creature, item, position, fromPosition)` [movements_area_damage.lua:areaDamage.onStepIn]
- `MoveEvent()` assigned to `areaDamage` [movements_area_damage.lua:areaDamage]
- `MoveEvent()` registration [movements_area_damage.lua:MoveEvent]
- `entrance.onStepIn(creature, item, position, fromPosition)` [movements_entrance.lua:entrance.onStepIn]
- `MoveEvent()` assigned to `entrance` [movements_entrance.lua:entrance]
- `MoveEvent()` registration [movements_entrance.lua:MoveEvent]
- `squares.onStepIn(creature, item, position, fromPosition)` [movements_squares.lua:squares.onStepIn]
- `MoveEvent()` assigned to `squares` [movements_squares.lua:squares]
- `MoveEvent()` registration [movements_squares.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_demon_oak.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_demon_oak_chest.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_demon_oak_gravestone.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_area_damage.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_entrance.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_entrance.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_squares.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_squares.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_demon_oak.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_demon_oak.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_demon_oak.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_demon_oak.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_demon_oak_chest.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_demon_oak_chest.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_demon_oak_chest.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_demon_oak_gravestone.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_demon_oak_gravestone.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [globalevents_demon_oak_voices.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_area_damage.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_entrance.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
