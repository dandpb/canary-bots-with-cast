# Sea Of Light

## Overview
Component package under `scripts/quests/sea_of_light` containing 1 files (`actions_sea_of_light.lua`..`actions_sea_of_light.lua`).

## Interface
- `rareCrystal.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_sea_of_light.lua:rareCrystal.onUse]
- `collectorCorpse.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_sea_of_light.lua:collectorCorpse.onUse]
- `Action()` assigned to `rareCrystal` [actions_sea_of_light.lua:rareCrystal]
- `Action()` assigned to `collectorCorpse` [actions_sea_of_light.lua:collectorCorpse]
- `Action()` registration [actions_sea_of_light.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_sea_of_light.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_sea_of_light.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_sea_of_light.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_sea_of_light.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_sea_of_light.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
