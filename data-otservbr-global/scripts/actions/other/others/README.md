# Others

## Overview
Component package under `scripts/actions/other/others` containing 2 files (`quest_system1.lua`..`quest_system2.lua`).

## Interface
- `copyContainerItem(originalContainer, newContainer)` [quest_system1.lua:copyContainerItem]
- `questSystem1.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [quest_system1.lua:questSystem1.onUse]
- `Action()` assigned to `questSystem1` [quest_system1.lua:questSystem1]
- `Action()` registration [quest_system1.lua:Action]
- `questSystem2.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [quest_system2.lua:questSystem2.onUse]
- `Action()` assigned to `questSystem2` [quest_system2.lua:questSystem2]
- `Action()` registration [quest_system2.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [quest_system1.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [quest_system2.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [quest_system1.lua:register]
- Mutates player or global storage state via `setStorageValue` [quest_system1.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [quest_system1.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [quest_system1.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [quest_system2.lua:register]
- Mutates player or global storage state via `setStorageValue` [quest_system2.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [quest_system2.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [quest_system2.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
