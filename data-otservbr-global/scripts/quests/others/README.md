# Others

## Overview
Component package under `scripts/quests/others` containing 12 files (`actions_calassa_comb_door.lua`..`actions_steal_from_thieves.lua`).

## Interface
- `othersCalassa.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_calassa_comb_door.lua:othersCalassa.onUse]
- `Action()` assigned to `othersCalassa` [actions_calassa_comb_door.lua:othersCalassa]
- `Action()` registration [actions_calassa_comb_door.lua:Action]
- `othersDeeper.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_deeper_banuta_shortcut.lua:othersDeeper.onUse]
- `Action()` assigned to `othersDeeper` [actions_deeper_banuta_shortcut.lua:othersDeeper]
- `Action()` registration [actions_deeper_banuta_shortcut.lua:Action]
- `othersEctoplasm.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ectoplasm_container.lua:othersEctoplasm.onUse]
- `Action()` assigned to `othersEctoplasm` [actions_ectoplasm_container.lua:othersEctoplasm]
- `Action()` registration [actions_ectoplasm_container.lua:Action]
- `exterminatorFlask.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_exterminator_flask.lua:exterminatorFlask.onUse]
- `Action()` assigned to `exterminatorFlask` [actions_exterminator_flask.lua:exterminatorFlask]
- `Action()` registration [actions_exterminator_flask.lua:Action]
- `revert(position, itemId, transformId)` [actions_fire_bug.lua:revert]
- `revertAshes()` [actions_fire_bug.lua:revertAshes]
- `othersFireBug.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_fire_bug.lua:othersFireBug.onUse]
- `Action()` assigned to `othersFireBug` [actions_fire_bug.lua:othersFireBug]
- `Action()` registration [actions_fire_bug.lua:Action]
- `gooeyMass.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_gooey_mass.lua:gooeyMass.onUse]
- `Action()` assigned to `gooeyMass` [actions_gooey_mass.lua:gooeyMass]
- `Action()` registration [actions_gooey_mass.lua:Action]
- `othersHellGate.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_hellgate_lever.lua:othersHellGate.onUse]
- `Action()` assigned to `othersHellGate` [actions_hellgate_lever.lua:othersHellGate]
- `Action()` registration [actions_hellgate_lever.lua:Action]
- `revertItem(position, itemId, transformId)` [actions_holy_water.lua:revertItem]
- `nexusMessage(player, message)` [actions_holy_water.lua:nexusMessage]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_calassa_comb_door.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_deeper_banuta_shortcut.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ectoplasm_container.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_exterminator_flask.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_fire_bug.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_fire_bug.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_gooey_mass.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_hellgate_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_holy_water.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_holy_water.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_orc_edron_lever.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_serpentine_tower_lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_calassa_comb_door.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_calassa_comb_door.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_calassa_comb_door.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_deeper_banuta_shortcut.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_deeper_banuta_shortcut.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_deeper_banuta_shortcut.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ectoplasm_container.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_ectoplasm_container.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_ectoplasm_container.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_exterminator_flask.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_exterminator_flask.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_exterminator_flask.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
