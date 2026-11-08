# The Gravedigger Of Drefia

## Overview
Component package under `scripts/quests/the_gravedigger_of_drefia` containing 29 files (`actions_amforas.lua`..`movements_teleport.lua`).

## Interface
- Defines 29 script/configuration files (`actions_amforas.lua` through `movements_teleport.lua`) [actions_amforas.lua]
- `gravediggerAmforas.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_amforas.lua:gravediggerAmforas.onUse]
- `Action()` assigned to `gravediggerAmforas` [actions_amforas.lua:gravediggerAmforas]
- `Action()` registration [actions_amforas.lua:Action]
- `gravediggerAshes.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ashes.lua:gravediggerAshes.onUse]
- `Action()` assigned to `gravediggerAshes` [actions_ashes.lua:gravediggerAshes]
- `Action()` registration [actions_ashes.lua:Action]
- `gravediggerBlood.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_blood.lua:gravediggerBlood.onUse]
- `Action()` assigned to `gravediggerBlood` [actions_blood.lua:gravediggerBlood]
- `Action()` registration [actions_blood.lua:Action]
- `gravediggerBones.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bones.lua:gravediggerBones.onUse]
- `Action()` assigned to `gravediggerBones` [actions_bones.lua:gravediggerBones]
- `Action()` registration [actions_bones.lua:Action]
- `gravediggerBook.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_bookcase.lua:gravediggerBook.onUse]
- `Action()` assigned to `gravediggerBook` [actions_bookcase.lua:gravediggerBook]
- `Action()` registration [actions_bookcase.lua:Action]
- `gravediggerBrain.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_brain.lua:gravediggerBrain.onUse]
- `Action()` assigned to `gravediggerBrain` [actions_brain.lua:gravediggerBrain]
- `Action()` registration [actions_brain.lua:Action]
- `gravediggerCaixa.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_caixa.lua:gravediggerCaixa.onUse]
- `Action()` assigned to `gravediggerCaixa` [actions_caixa.lua:gravediggerCaixa]
- `Action()` registration [actions_caixa.lua:Action]
- `gravediggerCandles.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_candles.lua:gravediggerCandles.onUse]
- `Action()` assigned to `gravediggerCandles` [actions_candles.lua:gravediggerCandles]
- `Action()` registration [actions_candles.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_amforas.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ashes.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_blood.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_bones.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_bookcase.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_brain.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_brain.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_caixa.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_candles.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_cape.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_chalk.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_flask.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_amforas.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_amforas.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_amforas.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ashes.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_ashes.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_ashes.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_blood.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_blood.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_blood.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bones.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_bones.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bones.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
