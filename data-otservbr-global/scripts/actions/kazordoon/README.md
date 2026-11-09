# Kazordoon

## Overview
Component package under `scripts/actions/kazordoon` containing 4 files (`elevator_lever.lua`..`trap_door.lua`).

## Interface
- `elevatorLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [elevator_lever.lua:elevatorLever.onUse]
- `Action()` assigned to `elevatorLever` [elevator_lever.lua:elevatorLever]
- `Action()` registration [elevator_lever.lua:Action]
- `oreWagons.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [ore_wagons.lua:oreWagons.onUse]
- `Action()` assigned to `oreWagons` [ore_wagons.lua:oreWagons]
- `Action()` registration [ore_wagons.lua:Action]
- `stone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [stone.lua:stone.onUse]
- `Action()` assigned to `stone` [stone.lua:stone]
- `Action()` registration [stone.lua:Action]
- `trapDoor.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [trap_door.lua:trapDoor.onUse]
- `Action()` assigned to `trapDoor` [trap_door.lua:trapDoor]
- `Action()` registration [trap_door.lua:Action]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [elevator_lever.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [elevator_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [ore_wagons.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [stone.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [trap_door.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [elevator_lever.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [elevator_lever.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [elevator_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [ore_wagons.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [ore_wagons.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [stone.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [stone.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [stone.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [trap_door.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [trap_door.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
