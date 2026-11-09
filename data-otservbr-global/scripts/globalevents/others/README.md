# Others

## Overview
Component package under `scripts/globalevents/others` containing 3 files (`check_mount.lua`..`raids_schedule.lua`).

## Interface
- `rentedMounts.onThink(interval)` [check_mount.lua:rentedMounts.onThink]
- `GlobalEvent("rentedmounts")` assigned to `rentedMounts` [check_mount.lua:rentedMounts]
- `GlobalEvent("rentedmounts")` registration [check_mount.lua:GlobalEvent]
- `loadMapActionsAndUniques()` [map_attributes_loader.lua:loadMapActionsAndUniques]
- `loadMapAttributes()` [map_attributes_loader.lua:loadMapAttributes]
- `resetGlobalStorages()` [map_attributes_loader.lua:resetGlobalStorages]
- `resetFerumbrasAscendantQuestHabitats()` [map_attributes_loader.lua:resetFerumbrasAscendantQuestHabitats]
- `mapAttributesLoader.onStartup()` [map_attributes_loader.lua:mapAttributesLoader.onStartup]
- `GlobalEvent("Map Attributes Loader")` assigned to `mapAttributesLoader` [map_attributes_loader.lua:mapAttributesLoader]
- `GlobalEvent("Map Attributes Loader")` registration [map_attributes_loader.lua:GlobalEvent]
- `spawnRaidsEvent.onThink(interval, lastExecution, thinkInterval)` [raids_schedule.lua:spawnRaidsEvent.onThink]
- `GlobalEvent("SpawnRaidsEvent")` assigned to `spawnRaidsEvent` [raids_schedule.lua:spawnRaidsEvent]
- `GlobalEvent("SpawnRaidsEvent")` registration [raids_schedule.lua:GlobalEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [check_mount.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [check_mount.lua:register]
- Mutates player or global storage state via `setStorageValue` [check_mount.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [map_attributes_loader.lua:register]
- Mutates player or global storage state via `setStorageValue` [map_attributes_loader.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [raids_schedule.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
