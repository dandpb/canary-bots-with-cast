# Ferumbras Ascension

## Overview
Component package under `scripts/quests/ferumbras_ascension` containing 66 files (`actions_bone_flute.lua`..`movements_zamulosh_teleport.lua`).

## Interface
- Defines 66 script/configuration files (`actions_bone_flute.lua` through `movements_zamulosh_teleport.lua`) [actions_bone_flute.lua]
- `ferumbrasAscendantBoneFlute.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bone_flute.lua:ferumbrasAscendantBoneFlute.onUse]
- `Action()` assigned to `ferumbrasAscendantBoneFlute` [actions_bone_flute.lua:ferumbrasAscendantBoneFlute]
- `Action()` registration [actions_bone_flute.lua:Action]
- `ferumbrasAscendantBoneWall.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bone_flute_wall.lua:ferumbrasAscendantBoneWall.onUse]
- `Action()` assigned to `ferumbrasAscendantBoneWall` [actions_bone_flute_wall.lua:ferumbrasAscendantBoneWall]
- `Action()` registration [actions_bone_flute_wall.lua:Action]
- `ferumbrasAscendantHomeComing.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_boots_of_homecoming.lua:ferumbrasAscendantHomeComing.onUse]
- `Action()` assigned to `ferumbrasAscendantHomeComing` [actions_boots_of_homecoming.lua:ferumbrasAscendantHomeComing]
- `Action()` registration [actions_boots_of_homecoming.lua:Action]
- `ferumbrasAscendantColorLevers.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_color_levers.lua:ferumbrasAscendantColorLevers.onUse]
- `Action()` assigned to `ferumbrasAscendantColorLevers` [actions_color_levers.lua:ferumbrasAscendantColorLevers]
- `Action()` registration [actions_color_levers.lua:Action]
- `BossLever(config)` assigned to `leverFerumbras` [actions_ferumbras_lever.lua:leverFerumbras]
- `BossLever(config)` registration [actions_ferumbras_lever.lua:BossLever]
- `revertItem(position, itemId, transformId)` [actions_flower_puzzle_lever.lua:revertItem]
- `ferumbrasAscendantFlowerPuzzle.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_flower_puzzle_lever.lua:ferumbrasAscendantFlowerPuzzle.onUse]
- `Action()` assigned to `ferumbrasAscendantFlowerPuzzle` [actions_flower_puzzle_lever.lua:ferumbrasAscendantFlowerPuzzle]
- `Action()` registration [actions_flower_puzzle_lever.lua:Action]
- `revertItem(position, itemId, transformId)` [actions_grave_flower.lua:revertItem]
- `ferumbrasAscendantGraveFlower.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_grave_flower.lua:ferumbrasAscendantGraveFlower.onUse]
- `Action()` assigned to `ferumbrasAscendantGraveFlower` [actions_grave_flower.lua:ferumbrasAscendantGraveFlower]
- `Action()` registration [actions_grave_flower.lua:Action]
- `transformArea()` [actions_habitat_corrupted.lua:transformArea]
- `resetFerumbrasAscendantHabitats(player)` [actions_habitat_corrupted.lua:resetFerumbrasAscendantHabitats]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_bone_flute.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_bone_flute_wall.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_boots_of_homecoming.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_color_levers.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_ferumbras_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_flower_puzzle_lever.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_flower_puzzle_lever.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_grave_flower.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_habitat_corrupted.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_habitat_corrupted.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_habitat_desert.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_habitat_desert.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bone_flute.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_bone_flute.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bone_flute.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bone_flute_wall.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_bone_flute_wall.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bone_flute_wall.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_boots_of_homecoming.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_boots_of_homecoming.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_boots_of_homecoming.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_color_levers.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_color_levers.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_color_levers.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
