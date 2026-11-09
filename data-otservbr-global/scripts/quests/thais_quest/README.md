# Thais Quest

## Overview
Component package under `scripts/quests/thais_quest` containing 1 files (`actions_life_ring_lever.lua`..`actions_life_ring_lever.lua`).

## Interface
- `othersLifeRing.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_life_ring_lever.lua:othersLifeRing.onUse]
- `Action()` assigned to `othersLifeRing` [actions_life_ring_lever.lua:othersLifeRing]
- `Action()` registration [actions_life_ring_lever.lua:Action]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_life_ring_lever.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_life_ring_lever.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_life_ring_lever.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_life_ring_lever.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
