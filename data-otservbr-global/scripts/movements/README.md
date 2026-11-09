# Movements

## Overview
Intermediate blueprint grouping 5 subdirectories under `scripts/movements`.

## Subdirectories & Boundaries
- [oramond](./oramond/README.md) - Component package under `scripts/movements/oramond` containing 6 files (`oramond_entrance.lua`..`voting_oramond.lua`).
- [others](./others/README.md) - Component package under `scripts/movements/others` containing 5 files (`dawnport_tiles.lua`..`walkback.lua`).
- [rookgaard](./rookgaard/README.md) - Component package under `scripts/movements/rookgaard` containing 3 files (`level_bridge.lua`..`rook_village.lua`).
- [roshamuul](./roshamuul/README.md) - Component package under `scripts/movements/roshamuul` containing 1 files (`strange_vortex_tp.lua`..`strange_vortex_tp.lua`).
- [teleport](./teleport/README.md) - Component package under `scripts/movements/teleport` containing 24 files (`adventurers_guild.lua`..`yalahar_demon.lua`).

## Interface
- `oramondEntrance.onStepIn(creature, item, position, fromPosition)` [oramond_entrance.lua:oramondEntrance.onStepIn]
- `MoveEvent()` assigned to `oramondEntrance` [oramond_entrance.lua:oramondEntrance]
- `chestRoomTile.onStepIn(creature, item, position, fromPosition)` [dawnport_tiles.lua:chestRoomTile.onStepIn]
- `templeStairs.onStepIn(creature, item, position, fromPosition)` [dawnport_tiles.lua:templeStairs.onStepIn]
- `levelBridge.onStepIn(creature, item, position, fromPosition)` [level_bridge.lua:levelBridge.onStepIn]
- `MoveEvent()` assigned to `levelBridge` [level_bridge.lua:levelBridge]
- `nightmareVortex.onStepIn(creature, item, position, fromPosition)` [strange_vortex_tp.lua:nightmareVortex.onStepIn]
- `MoveEvent()` assigned to `nightmareVortex` [strange_vortex_tp.lua:nightmareVortex]
- `adventurersGuild.onStepIn(creature, item, position, fromPosition)` [adventurers_guild.lua:adventurersGuild.onStepIn]
- `MoveEvent()` assigned to `adventurersGuild` [adventurers_guild.lua:adventurersGuild]
- [oramond](./oramond/README.md) - Component package under `scripts/movements/oramond` containing 6 files (`oramond_entrance.lua`..`voting_oramond.lua`).
- [others](./others/README.md) - Component package under `scripts/movements/others` containing 5 files (`dawnport_tiles.lua`..`walkback.lua`).
- [rookgaard](./rookgaard/README.md) - Component package under `scripts/movements/rookgaard` containing 3 files (`level_bridge.lua`..`rook_village.lua`).
- [roshamuul](./roshamuul/README.md) - Component package under `scripts/movements/roshamuul` containing 1 files (`strange_vortex_tp.lua`..`strange_vortex_tp.lua`).
- [teleport](./teleport/README.md) - Component package under `scripts/movements/teleport` containing 24 files (`adventurers_guild.lua`..`yalahar_demon.lua`).

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [oramond_entrance.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [dawnport_tiles.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [level_bridge.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [strange_vortex_tp.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [adventurers_guild.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [oramond_entrance.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [dawnport_tiles.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [level_bridge.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [strange_vortex_tp.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [adventurers_guild.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
