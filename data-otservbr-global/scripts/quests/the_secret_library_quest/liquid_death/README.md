# Liquid Death

## Overview
Component package under `scripts/quests/the_secret_library_quest/liquid_death` containing 4 files (`actions_brokulLever.lua`..`movements_teleportTo.lua`).

## Interface
- `BossLever(config)` assigned to `leverBrokul` [actions_brokulLever.lua:leverBrokul]
- `BossLever(config)` registration [actions_brokulLever.lua:BossLever]
- `doRevert(position, id, newId)` [actions_usableItens.lua:doRevert]
- `fixStatue(position, id)` [actions_usableItens.lua:fixStatue]
- `actions_liquid_usableItens.onUse(player, item, position, fromPosition, pos, target, toPosition)` [actions_usableItens.lua:actions_liquid_usableItens.onUse]
- `Action()` assigned to `actions_liquid_usableItens` [actions_usableItens.lua:actions_liquid_usableItens]
- `Action()` registration [actions_usableItens.lua:Action]
- `movements_liquid_bossWay.onStepIn(creature, item, position, fromPosition)` [movements_bossWay.lua:movements_liquid_bossWay.onStepIn]
- `MoveEvent()` assigned to `movements_liquid_bossWay` [movements_bossWay.lua:movements_liquid_bossWay]
- `MoveEvent()` registration [movements_bossWay.lua:MoveEvent]
- `movements_liquid_teleportTo.onStepIn(creature, item, position, fromPosition)` [movements_teleportTo.lua:movements_liquid_teleportTo.onStepIn]
- `MoveEvent()` assigned to `movements_liquid_teleportTo` [movements_teleportTo.lua:movements_liquid_teleportTo]
- `MoveEvent()` registration [movements_teleportTo.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_brokulLever.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_brokulLever.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_usableItens.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_usableItens.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_bossWay.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_bossWay.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_teleportTo.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_teleportTo.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_brokulLever.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_usableItens.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_usableItens.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_usableItens.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_usableItens.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_bossWay.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_bossWay.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_teleportTo.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_teleportTo.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_teleportTo.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
