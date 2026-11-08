# In Service Of Yalahar

## Overview
Component package under `scripts/quests/in_service_of_yalahar` containing 18 files (`actions_charm.lua`..`quara_leader_kill.lua`).

## Interface
- `inServiceYalaharCharm.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_charm.lua:inServiceYalaharCharm.onUse]
- `Action()` assigned to `inServiceYalaharCharm` [actions_charm.lua:inServiceYalaharCharm]
- `Action()` registration [actions_charm.lua:Action]
- `inServiceYalaharFormula.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_formula.lua:inServiceYalaharFormula.onUse]
- `Action()` assigned to `inServiceYalaharFormula` [actions_formula.lua:inServiceYalaharFormula]
- `Action()` registration [actions_formula.lua:Action]
- `inServiceYalaharGhost.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ghost.lua:inServiceYalaharGhost.onUse]
- `Action()` assigned to `inServiceYalaharGhost` [actions_ghost.lua:inServiceYalaharGhost]
- `Action()` registration [actions_ghost.lua:Action]
- `doClearAreaAzerus()` [actions_last_fight.lua:doClearAreaAzerus]
- `doChangeAzerus()` [actions_last_fight.lua:doChangeAzerus]
- `summonMonster(name, position)` [actions_last_fight.lua:summonMonster]
- `inServiceYalaharLastFight.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_last_fight.lua:inServiceYalaharLastFight.onUse]
- `Action()` assigned to `inServiceYalaharLastFight` [actions_last_fight.lua:inServiceYalaharLastFight]
- `Action()` registration [actions_last_fight.lua:Action]
- `inServiceYalaharMatrix.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_matrix.lua:inServiceYalaharMatrix.onUse]
- `Action()` assigned to `inServiceYalaharMatrix` [actions_matrix.lua:inServiceYalaharMatrix]
- `Action()` registration [actions_matrix.lua:Action]
- `inServiceYalaharMechanism.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mechanism.lua:inServiceYalaharMechanism.onUse]
- `Action()` assigned to `inServiceYalaharMechanism` [actions_mechanism.lua:inServiceYalaharMechanism]
- `Action()` registration [actions_mechanism.lua:Action]
- `inServiceYalaharMorik.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_morik_summon.lua:inServiceYalaharMorik.onUse]
- `Action()` assigned to `inServiceYalaharMorik` [actions_morik_summon.lua:inServiceYalaharMorik]
- `Action()` registration [actions_morik_summon.lua:Action]
- `inServiceYalaharWest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mr_west_door.lua:inServiceYalaharWest.onUse]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_charm.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_ghost.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_last_fight.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_matrix.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mechanism.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_morik_summon.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mr_west_door.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_reward.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_yalahar_machine_war_golems.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescritps_azerus_kill.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescritps_diseased_trio_kill.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_demon_teleport.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_charm.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_charm.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_charm.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_formula.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_formula.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_formula.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ghost.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_ghost.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_ghost.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_ghost.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_last_fight.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_last_fight.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
