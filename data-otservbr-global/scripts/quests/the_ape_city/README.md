# The Ape City

## Overview
Component package under `scripts/quests/the_ape_city` containing 4 files (`actions_mission09_snake_destroyer.lua`..`movements_mission9_the_deepest_catacomb_teleport.lua`).

## Interface
- `theApeMiss9.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission09_snake_destroyer.lua:theApeMiss9.onUse]
- `Action()` assigned to `theApeMiss9` [actions_mission09_snake_destroyer.lua:theApeMiss9]
- `Action()` registration [actions_mission09_snake_destroyer.lua:Action]
- `revertLever(position)` [actions_mission9_catacombs_lever.lua:revertLever]
- `revertWall(position)` [actions_mission9_catacombs_lever.lua:revertWall]
- `lever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission9_catacombs_lever.lua:lever.onUse]
- `wallRemove(player, item)` [actions_mission9_catacombs_lever.lua:wallRemove]
- `gate.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mission9_catacombs_lever.lua:gate.onUse]
- `Action()` assigned to `lever` [actions_mission9_catacombs_lever.lua:lever]
- `Action()` assigned to `gate` [actions_mission9_catacombs_lever.lua:gate]
- `Action()` registration [actions_mission9_catacombs_lever.lua:Action]
- `mission4ParchmentDecyphering.onStepIn(creature, item, position, fromPosition)` [movements_mission4_parchment_decyphering.lua:mission4ParchmentDecyphering.onStepIn]
- `MoveEvent()` assigned to `mission4ParchmentDecyphering` [movements_mission4_parchment_decyphering.lua:mission4ParchmentDecyphering]
- `MoveEvent()` registration [movements_mission4_parchment_decyphering.lua:MoveEvent]
- `mission9TheDeepestCatacombTeleport.onStepIn(creature, item, position, fromPosition)` [movements_mission9_the_deepest_catacomb_teleport.lua:mission9TheDeepestCatacombTeleport.onStepIn]
- `MoveEvent()` assigned to `mission9TheDeepestCatacombTeleport` [movements_mission9_the_deepest_catacomb_teleport.lua:mission9TheDeepestCatacombTeleport]
- `MoveEvent()` registration [movements_mission9_the_deepest_catacomb_teleport.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mission09_snake_destroyer.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_mission9_catacombs_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_mission4_parchment_decyphering.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_mission4_parchment_decyphering.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_mission9_the_deepest_catacomb_teleport.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_mission9_the_deepest_catacomb_teleport.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission09_snake_destroyer.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_mission09_snake_destroyer.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mission09_snake_destroyer.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mission9_catacombs_lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_mission9_catacombs_lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mission9_catacombs_lever.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_mission9_catacombs_lever.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_mission4_parchment_decyphering.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_mission4_parchment_decyphering.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_mission9_the_deepest_catacomb_teleport.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_mission9_the_deepest_catacomb_teleport.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_mission9_the_deepest_catacomb_teleport.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
