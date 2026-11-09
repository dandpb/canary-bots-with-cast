# The Pits Of Inferno Quest

## Overview
Component package under `scripts/quests/the_pits_of_inferno_quest` containing 26 files (`actions_bazir_maze_lever.lua`..`movements_trap.lua`).

## Interface
- Defines 26 script/configuration files (`actions_bazir_maze_lever.lua` through `movements_trap.lua`) [actions_bazir_maze_lever.lua]
- `pitsOfInfernoMazeLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bazir_maze_lever.lua:pitsOfInfernoMazeLever.onUse]
- `Action()` assigned to `pitsOfInfernoMazeLever` [actions_bazir_maze_lever.lua:pitsOfInfernoMazeLever]
- `Action()` registration [actions_bazir_maze_lever.lua:Action]
- `pitsOfInfernoBlackMirror.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bazir_mirror.lua:pitsOfInfernoBlackMirror.onUse]
- `Action()` assigned to `pitsOfInfernoBlackMirror` [actions_bazir_mirror.lua:pitsOfInfernoBlackMirror]
- `Action()` registration [actions_bazir_mirror.lua:Action]
- `pitsOfInfernoWrongLevers.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bazir_wrong_levers.lua:pitsOfInfernoWrongLevers.onUse]
- `Action()` assigned to `pitsOfInfernoWrongLevers` [actions_bazir_wrong_levers.lua:pitsOfInfernoWrongLevers]
- `Action()` registration [actions_bazir_wrong_levers.lua:Action]
- `pitsOfInfernoFirstThroneLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_fire_throne_lever.lua:pitsOfInfernoFirstThroneLever.onUse]
- `Action()` assigned to `pitsOfInfernoFirstThroneLever` [actions_fire_throne_lever.lua:pitsOfInfernoFirstThroneLever]
- `Action()` registration [actions_fire_throne_lever.lua:Action]
- `pitsOfInfernoFountain.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_fountain.lua:pitsOfInfernoFountain.onUse]
- `Action()` assigned to `pitsOfInfernoFountain` [actions_fountain.lua:pitsOfInfernoFountain]
- `Action()` registration [actions_fountain.lua:Action]
- `pitsOfInfernoLadderLevers.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ladder_levers.lua:pitsOfInfernoLadderLevers.onUse]
- `Action()` assigned to `pitsOfInfernoLadderLevers` [actions_ladder_levers.lua:pitsOfInfernoLadderLevers]
- `Action()` registration [actions_ladder_levers.lua:Action]
- `createStones()` [actions_levers.lua:createStones]
- `revertLever(position)` [actions_levers.lua:revertLever]
- `pitsOfInfernoLevers.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_levers.lua:pitsOfInfernoLevers.onUse]
- `Action()` assigned to `pitsOfInfernoLevers` [actions_levers.lua:pitsOfInfernoLevers]
- `Action()` registration [actions_levers.lua:Action]
- `pitsOfInfernoMazeStone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_maze_stone.lua:pitsOfInfernoMazeStone.onUse]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_bazir_maze_lever.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_bazir_mirror.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_fire_throne_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_fountain.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_ladder_levers.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_levers.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_levers.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_maze_stone.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_oil.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_stone_lever.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_trap_lever.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_walls.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bazir_maze_lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_bazir_maze_lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bazir_maze_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bazir_mirror.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_bazir_mirror.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bazir_wrong_levers.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_bazir_wrong_levers.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bazir_wrong_levers.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_fire_throne_lever.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_fire_throne_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_fountain.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_fountain.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
