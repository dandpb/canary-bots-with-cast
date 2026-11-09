# Probing

## Overview
Component package under `scripts/quests/oramond/probing` containing 1 files (`actions_mono_detector_strange_probing_device.lua`..`actions_mono_detector_strange_probing_device.lua`).

## Interface
- `isPositionInArea(pos, area)` [actions_mono_detector_strange_probing_device.lua:isPositionInArea]
- `getRandomPositionInPrimaryArea()` [actions_mono_detector_strange_probing_device.lua:getRandomPositionInPrimaryArea]
- `getRandomPositionInSecondaryArea()` [actions_mono_detector_strange_probing_device.lua:getRandomPositionInSecondaryArea]
- `actions_mono_detector.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mono_detector_strange_probing_device.lua:actions_mono_detector.onUse]
- `actions_strange_probing_device.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mono_detector_strange_probing_device.lua:actions_strange_probing_device.onUse]
- `Action()` assigned to `actions_mono_detector` [actions_mono_detector_strange_probing_device.lua:actions_mono_detector]
- `Action()` assigned to `actions_strange_probing_device` [actions_mono_detector_strange_probing_device.lua:actions_strange_probing_device]
- `Action()` registration [actions_mono_detector_strange_probing_device.lua:Action]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mono_detector_strange_probing_device.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mono_detector_strange_probing_device.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_mono_detector_strange_probing_device.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mono_detector_strange_probing_device.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
