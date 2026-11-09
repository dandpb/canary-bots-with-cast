# Tools

## Overview
Component package under `scripts/actions/tools` containing 11 files (`bricklayer_kit.lua`..`spiked_squelcher.lua`).

## Interface
- `brickLayerKit.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [bricklayer_kit.lua:brickLayerKit.onUse]
- `Action()` assigned to `brickLayerKit` [bricklayer_kit.lua:brickLayerKit]
- `Action()` registration [bricklayer_kit.lua:Action]
- `grinder.onUse(player, item, frompos, item2, topos)` [grinder.lua:grinder.onUse]
- `Action()` assigned to `grinder` [grinder.lua:grinder]
- `Action()` registration [grinder.lua:Action]
- `createWooden(position, removeId, createId, actionId)` [hammer.lua:createWooden]
- `hammer.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [hammer.lua:hammer.onUse]
- `Action()` assigned to `hammer` [hammer.lua:hammer]
- `Action()` registration [hammer.lua:Action]
- `juiceSqueezer.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [juice_squeezer.lua:juiceSqueezer.onUse]
- `Action()` assigned to `juiceSqueezer` [juice_squeezer.lua:juiceSqueezer]
- `Action()` registration [juice_squeezer.lua:Action]
- `lockPick.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [lock_pick.lua:lockPick.onUse]
- `Action()` assigned to `lockPick` [lock_pick.lua:lockPick]
- `Action()` registration [lock_pick.lua:Action]
- `metalFile.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [metal_file.lua:metalFile.onUse]
- `Action()` assigned to `metalFile` [metal_file.lua:metalFile]
- `Action()` registration [metal_file.lua:Action]
- `present.onUse(cid, item, fromPosition, itemEx, toPosition)` [present.lua:present.onUse]
- `Action()` assigned to `present` [present.lua:present]
- `Action()` registration [present.lua:Action]
- `rake.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [rake.lua:rake.onUse]
- `Action()` assigned to `rake` [rake.lua:rake]
- `Action()` registration [rake.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [hammer.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [hammer.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [lock_pick.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [rake.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [skinning.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [skinning.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [bricklayer_kit.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [bricklayer_kit.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [bricklayer_kit.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [grinder.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [hammer.lua:register]
- Mutates player or global storage state via `setStorageValue` [hammer.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [hammer.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [hammer.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [hammer.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [juice_squeezer.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [juice_squeezer.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [lock_pick.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
