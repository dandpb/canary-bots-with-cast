# Killing In The Name Of

## Overview
Component package under `scripts/quests/killing_in_the_name_of` containing 3 files (`creaturescripts_boss_kill.lua`..`movements_boss.lua`).

## Interface
- `deathEvent.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_boss_kill.lua:deathEvent.onDeath]
- `serverstartup.onStartup()` [creaturescripts_boss_kill.lua:serverstartup.onStartup]
- `CreatureEvent("KillingInTheNameOfBossDeath")` assigned to `deathEvent` [creaturescripts_boss_kill.lua:deathEvent]
- `CreatureEvent("KillingInTheNameOfBossDeath")` registration [creaturescripts_boss_kill.lua:CreatureEvent]
- `GlobalEvent("KillingInTheNameOfBossDeathStartup")` assigned to `serverstartup` [creaturescripts_boss_kill.lua:serverstartup]
- `GlobalEvent("KillingInTheNameOfBossDeathStartup")` registration [creaturescripts_boss_kill.lua:GlobalEvent]
- `killCheck(player, targetName, taskName, taskStage, taskInfo, taskAltKillCount, taskkillCount)` [creaturescripts_monster_kill.lua:killCheck]
- `deathEvent.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_monster_kill.lua:deathEvent.onDeath]
- `serverstartup.onStartup()` [creaturescripts_monster_kill.lua:serverstartup.onStartup]
- `CreatureEvent("KillingInTheNameOfMonsterDeath")` assigned to `deathEvent` [creaturescripts_monster_kill.lua:deathEvent]
- `CreatureEvent("KillingInTheNameOfMonsterDeath")` registration [creaturescripts_monster_kill.lua:CreatureEvent]
- `GlobalEvent("KillingInTheNameOfMonsterDeathStartup")` assigned to `serverstartup` [creaturescripts_monster_kill.lua:serverstartup]
- `GlobalEvent("KillingInTheNameOfMonsterDeathStartup")` registration [creaturescripts_monster_kill.lua:GlobalEvent]
- `boss.onStepIn(creature, item, position, fromPosition)` [movements_boss.lua:boss.onStepIn]
- `MoveEvent()` assigned to `boss` [movements_boss.lua:boss]
- `MoveEvent()` registration [movements_boss.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_boss_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_monster_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_boss.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_boss.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_boss_kill.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_boss_kill.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_monster_kill.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_monster_kill.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_boss.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_boss.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [movements_boss.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_boss.lua:teleportTo]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [movements_boss.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
