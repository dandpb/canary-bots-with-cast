# The Order Of The Falcon

## Overview
Component package under `scripts/quests/the_secret_library_quest/the_order_of_the_falcon` containing 4 files (`actions_doors.lua`..`movements_bossEntrance.lua`).

## Interface
- `actions_falcon_doors.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_doors.lua:actions_falcon_doors.onUse]
- `Action()` assigned to `actions_falcon_doors` [actions_doors.lua:actions_falcon_doors]
- `Action()` registration [actions_doors.lua:Action]
- `actions_entrance.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_entrance.lua:actions_entrance.onUse]
- `Action()` assigned to `actions_entrance` [actions_entrance.lua:actions_entrance]
- `Action()` registration [actions_entrance.lua:Action]
- `BossLever(config)` assigned to `leverOberon` [actions_oberonLever.lua:leverOberon]
- `BossLever(config)` registration [actions_oberonLever.lua:BossLever]
- `movements_falcon_bossEntrance.onStepIn(creature, item, position, fromPosition)` [movements_bossEntrance.lua:movements_falcon_bossEntrance.onStepIn]
- `MoveEvent()` assigned to `movements_falcon_bossEntrance` [movements_bossEntrance.lua:movements_falcon_bossEntrance]
- `MoveEvent()` registration [movements_bossEntrance.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_doors.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_doors.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_bossEntrance.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_bossEntrance.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_doors.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_doors.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_doors.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_entrance.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_entrance.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_entrance.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_oberonLever.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_oberonLever.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_oberonLever.lua:Game]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_bossEntrance.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_bossEntrance.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
