# Rottin Wood And Married Men

## Overview
Component package under `scripts/quests/rottin_wood_and_married_men` containing 3 files (`actions_broken_wall.lua`..`actions_trap.lua`).

## Interface
- `rottinWoodBroken.onUse(player, item, fromPosition, itemEx, toPosition, isHotkey)` [actions_broken_wall.lua:rottinWoodBroken.onUse]
- `Action()` assigned to `rottinWoodBroken` [actions_broken_wall.lua:rottinWoodBroken]
- `Action()` registration [actions_broken_wall.lua:Action]
- `rottinWoodCorpse.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_corpse.lua:rottinWoodCorpse.onUse]
- `Action()` assigned to `rottinWoodCorpse` [actions_corpse.lua:rottinWoodCorpse]
- `Action()` registration [actions_corpse.lua:Action]
- `removeMonster()` [actions_trap.lua:removeMonster]
- `removeTrap()` [actions_trap.lua:removeTrap]
- `removeItems()` [actions_trap.lua:removeItems]
- `rottinWoodtrap.onUse(cid, item, fromPosition, itemEx, toPosition, isHotkey)` [actions_trap.lua:rottinWoodtrap.onUse]
- `Action()` assigned to `rottinWoodtrap` [actions_trap.lua:rottinWoodtrap]
- `Action()` registration [actions_trap.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_broken_wall.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_corpse.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_trap.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_broken_wall.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_broken_wall.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_broken_wall.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_corpse.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_corpse.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_corpse.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_trap.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_trap.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_trap.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_trap.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
