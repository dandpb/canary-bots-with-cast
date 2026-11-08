# Spike Tasks

## Overview
Component package under `scripts/quests/spike_tasks` containing 10 files (`actions_fertilizer.lua`..`creaturescripts_upper_spike_kill.lua`).

## Interface
- `spikeTasksFertilizer.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_fertilizer.lua:spikeTasksFertilizer.onUse]
- `Action()` assigned to `spikeTasksFertilizer` [actions_fertilizer.lua:spikeTasksFertilizer]
- `Action()` registration [actions_fertilizer.lua:Action]
- `getSearchString(fromPos, toPos)` [actions_ghost_detector.lua:getSearchString]
- `spikeTasksGhost.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ghost_detector.lua:spikeTasksGhost.onUse]
- `Action()` assigned to `spikeTasksGhost` [actions_ghost_detector.lua:spikeTasksGhost]
- `Action()` registration [actions_ghost_detector.lua:Action]
- `spikeTasksStone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lode_stone.lua:spikeTasksStone.onUse]
- `Action()` assigned to `spikeTasksStone` [actions_lode_stone.lua:spikeTasksStone]
- `Action()` registration [actions_lode_stone.lua:Action]
- `spikeTasksNests.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_nests.lua:spikeTasksNests.onUse]
- `Action()` assigned to `spikeTasksNests` [actions_nests.lua:spikeTasksNests]
- `Action()` registration [actions_nests.lua:Action]
- `spikeTasksShovel.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_spirit_shovel.lua:spikeTasksShovel.onUse]
- `Action()` assigned to `spikeTasksShovel` [actions_spirit_shovel.lua:spikeTasksShovel]
- `Action()` registration [actions_spirit_shovel.lua:Action]
- `spikeTasksThermometer.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_thermometer.lua:spikeTasksThermometer.onUse]
- `Action()` assigned to `spikeTasksThermometer` [actions_thermometer.lua:spikeTasksThermometer]
- `Action()` registration [actions_thermometer.lua:Action]
- `spikeTasksFork.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_tuning_fork.lua:spikeTasksFork.onUse]
- `Action()` assigned to `spikeTasksFork` [actions_tuning_fork.lua:spikeTasksFork]
- `Action()` registration [actions_tuning_fork.lua:Action]
- `lowerSpikeKill.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_lower_spike_kill.lua:lowerSpikeKill.onDeath]
- `CreatureEvent("LowerSpikeDeath")` assigned to `lowerSpikeKill` [creaturescripts_lower_spike_kill.lua:lowerSpikeKill]
- `CreatureEvent("LowerSpikeDeath")` registration [creaturescripts_lower_spike_kill.lua:CreatureEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_fertilizer.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ghost_detector.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lode_stone.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_nests.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_spirit_shovel.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_thermometer.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_tuning_fork.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_lower_spike_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_middle_spike_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_upper_spike_kill.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_fertilizer.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_fertilizer.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_fertilizer.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ghost_detector.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_ghost_detector.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_ghost_detector.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lode_stone.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_lode_stone.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_lode_stone.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_lode_stone.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_nests.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_nests.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
