# The Explorer Society

## Overview
Component package under `scripts/quests/the_explorer_society` containing 11 files (`actions_botanist.lua`..`movements_carvingteleport_port_hope.lua`).

## Interface
- `explorerSocietyBotanist.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_botanist.lua:explorerSocietyBotanist.onUse]
- `Action()` assigned to `explorerSocietyBotanist` [actions_botanist.lua:explorerSocietyBotanist]
- `Action()` registration [actions_botanist.lua:Action]
- `explorerSocietyButterfly.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_butterfly.lua:explorerSocietyButterfly.onUse]
- `Action()` assigned to `explorerSocietyButterfly` [actions_butterfly.lua:explorerSocietyButterfly]
- `Action()` registration [actions_butterfly.lua:Action]
- `explorerSocietyDragon.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_dragon.lua:explorerSocietyDragon.onUse]
- `Action()` assigned to `explorerSocietyDragon` [actions_dragon.lua:explorerSocietyDragon]
- `Action()` registration [actions_dragon.lua:Action]
- `explorerSocietyFindings.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_findings.lua:explorerSocietyFindings.onUse]
- `Action()` assigned to `explorerSocietyFindings` [actions_findings.lua:explorerSocietyFindings]
- `Action()` registration [actions_findings.lua:Action]
- `explorerSocietyIcicle.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_icicle.lua:explorerSocietyIcicle.onUse]
- `Action()` assigned to `explorerSocietyIcicle` [actions_icicle.lua:explorerSocietyIcicle]
- `Action()` registration [actions_icicle.lua:Action]
- `explorerSocietyResonance.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_resonance.lua:explorerSocietyResonance.onUse]
- `Action()` assigned to `explorerSocietyResonance` [actions_resonance.lua:explorerSocietyResonance]
- `Action()` registration [actions_resonance.lua:Action]
- `explorerSocietyStone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_stone.lua:explorerSocietyStone.onUse]
- `Action()` assigned to `explorerSocietyStone` [actions_stone.lua:explorerSocietyStone]
- `Action()` registration [actions_stone.lua:Action]
- `explorerSocietyPaper.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_tracing_paper.lua:explorerSocietyPaper.onUse]
- `Action()` assigned to `explorerSocietyPaper` [actions_tracing_paper.lua:explorerSocietyPaper]
- `Action()` registration [actions_tracing_paper.lua:Action]
- `calassa.onStepIn(creature, item, position, fromPosition)` [movements_calassa.lua:calassa.onStepIn]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_botanist.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_butterfly.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_dragon.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_findings.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_icicle.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_resonance.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_stone.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_tracing_paper.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_calassa.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_carving_teleport_liberty_bay.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_carving_teleport_liberty_bay.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_carvingteleport_port_hope.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_botanist.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_botanist.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_botanist.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_butterfly.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_butterfly.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_butterfly.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_dragon.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_dragon.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_dragon.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_findings.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_findings.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_findings.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
