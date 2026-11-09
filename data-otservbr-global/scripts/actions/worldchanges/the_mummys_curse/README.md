# The Mummys Curse

## Overview
Component package under `scripts/actions/worldchanges/the_mummys_curse` containing 1 files (`horestis_jars.lua`..`horestis_jars.lua`).

## Interface
- `createWall()` [horestis_jars.lua:createWall]
- `horestisJars.onUse(cid, item, fromPosition, itemEx, toPosition)` [horestis_jars.lua:horestisJars.onUse]
- `Action()` assigned to `horestisJars` [horestis_jars.lua:horestisJars]
- `Action()` registration [horestis_jars.lua:Action]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [horestis_jars.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [horestis_jars.lua:Game]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [horestis_jars.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
