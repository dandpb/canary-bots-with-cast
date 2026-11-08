# Children Of The Revolution

## Overview
Component package under `scripts/quests/children_of_the_revolution` containing 11 files (`actions_mission3_chest.lua`..`movements_temple.lua`).

## Interface
- `childrenMission3.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission3_chest.lua:childrenMission3.onUse]
- `Action()` assigned to `childrenMission3` [actions_mission3_chest.lua:childrenMission3]
- `Action()` registration [actions_mission3_chest.lua:Action]
- `childrenPoison.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission3_poison_water.lua:childrenPoison.onUse]
- `Action()` assigned to `childrenPoison` [actions_mission3_poison_water.lua:childrenPoison]
- `Action()` registration [actions_mission3_poison_water.lua:Action]
- `childrenGrease.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission4_grease_oil.lua:childrenGrease.onUse]
- `Action()` assigned to `childrenGrease` [actions_mission4_grease_oil.lua:childrenGrease]
- `Action()` registration [actions_mission4_grease_oil.lua:Action]
- `puzzle(position, itemId, itemTransform)` [actions_mission4_levers_puzzle.lua:puzzle]
- `revertLever(fromPosition)` [actions_mission4_levers_puzzle.lua:revertLever]
- `childrenGrease.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission4_levers_puzzle.lua:childrenGrease.onUse]
- `Action()` assigned to `childrenGrease` [actions_mission4_levers_puzzle.lua:childrenGrease]
- `Action()` registration [actions_mission4_levers_puzzle.lua:Action]
- `childrenZalamon.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_zalamon_door.lua:childrenZalamon.onUse]
- `Action()` assigned to `childrenZalamon` [actions_zalamon_door.lua:childrenZalamon]
- `Action()` registration [actions_zalamon_door.lua:Action]
- `doClearMissionArea()` [movements_click.lua:doClearMissionArea]
- `removeStairs()` [movements_click.lua:removeStairs]
- `summonWave(i)` [movements_click.lua:summonWave]
- `click.onStepIn(creature, item, position, fromPosition)` [movements_click.lua:click.onStepIn]
- `MoveEvent()` assigned to `click` [movements_click.lua:click]
- `MoveEvent()` registration [movements_click.lua:MoveEvent]
- `spy.onStepIn(creature, item, position, fromPosition)` [movements_spy.lua:spy.onStepIn]
- `MoveEvent()` assigned to `spy` [movements_spy.lua:spy]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission3_chest.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission3_poison_water.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission4_grease_oil.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission4_levers_puzzle.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_mission4_levers_puzzle.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_zalamon_door.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_click.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_click.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movements_click.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_spy.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_spy.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_stair.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission3_chest.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_mission3_chest.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mission3_chest.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission3_poison_water.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_mission3_poison_water.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mission3_poison_water.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission4_grease_oil.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_mission4_grease_oil.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mission4_grease_oil.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission4_levers_puzzle.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_mission4_levers_puzzle.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mission4_levers_puzzle.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
