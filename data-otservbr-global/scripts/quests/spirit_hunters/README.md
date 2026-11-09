# Spirit Hunters

## Overview
Component package under `scripts/quests/spirit_hunters` containing 1 files (`actions_magical_device.lua`..`actions_magical_device.lua`).

## Interface
- `spiritMagical.onUse(cid, item, fromPosition, itemEx, toPosition)` [actions_magical_device.lua:spiritMagical.onUse]
- `Action()` assigned to `spiritMagical` [actions_magical_device.lua:spiritMagical]
- `Action()` registration [actions_magical_device.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_magical_device.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_magical_device.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_magical_device.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_magical_device.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_magical_device.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
