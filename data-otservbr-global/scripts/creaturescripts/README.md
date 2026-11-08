# Creaturescripts

## Overview
Intermediate blueprint grouping 3 subdirectories under `scripts/creaturescripts`.

## Subdirectories & Boundaries
- [customs](./customs/README.md) - Component package under `scripts/creaturescripts/customs` containing 2 files (`freequests.lua`..`reward_exercise.lua`).
- [monster](./monster/README.md) - Component package under `scripts/creaturescripts/monster` containing 18 files (`gaz_haragoth_heal.lua`..`zavarash_hide.lua`).
- [others](./others/README.md) - Component package under `scripts/creaturescripts/others` containing 5 files (`dawnport.lua`..`rookgaard_advance.lua`).

## Interface
- `playerFreeQuestStart(playerId, index)` [freequests.lua:playerFreeQuestStart]
- `freeQuests.onLogin(player)` [freequests.lua:freeQuests.onLogin]
- `gazHaragothHeal.onThink(creature)` [gaz_haragoth_heal.lua:gazHaragothHeal.onThink]
- `CreatureEvent("GazHaragothHeal")` assigned to `gazHaragothHeal` [gaz_haragoth_heal.lua:gazHaragothHeal]
- `teleportToDawnportTemple(uid)` [dawnport.lua:teleportToDawnportTemple]
- `dawnportAdvance.onAdvance(player, skill, oldLevel, newLevel)` [dawnport.lua:dawnportAdvance.onAdvance]
- [customs](./customs/README.md) - Component package under `scripts/creaturescripts/customs` containing 2 files (`freequests.lua`..`reward_exercise.lua`).
- [monster](./monster/README.md) - Component package under `scripts/creaturescripts/monster` containing 18 files (`gaz_haragoth_heal.lua`..`zavarash_hide.lua`).
- [others](./others/README.md) - Component package under `scripts/creaturescripts/others` containing 5 files (`dawnport.lua`..`rookgaard_advance.lua`).

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [freequests.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [minion_gaz_haragoth_vortex.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [dawnport.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [freequests.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [gaz_haragoth_heal.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [dawnport.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
