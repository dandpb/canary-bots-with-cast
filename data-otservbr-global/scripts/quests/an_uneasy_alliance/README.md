# An Uneasy Alliance

## Overview
Component package under `scripts/quests/an_uneasy_alliance` containing 2 files (`actions_crystal_ball.lua`..`creaturescripts_renegade_orc_kill.lua`).

## Interface
- `revert(position)` [actions_crystal_ball.lua:revert]
- `crystalball.onUse(player, item, fromPosition, target, toPosition)` [actions_crystal_ball.lua:crystalball.onUse]
- `Action()` assigned to `crystalball` [actions_crystal_ball.lua:crystalball]
- `Action()` registration [actions_crystal_ball.lua:Action]
- `renegadeOrcKill.onDeath(creature)` [creaturescripts_renegade_orc_kill.lua:renegadeOrcKill.onDeath]
- `CreatureEvent("RenegadeOrcDeath")` assigned to `renegadeOrcKill` [creaturescripts_renegade_orc_kill.lua:renegadeOrcKill]
- `CreatureEvent("RenegadeOrcDeath")` registration [creaturescripts_renegade_orc_kill.lua:CreatureEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_crystal_ball.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_crystal_ball.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_renegade_orc_kill.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_crystal_ball.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_crystal_ball.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_crystal_ball.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_crystal_ball.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_renegade_orc_kill.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_renegade_orc_kill.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
