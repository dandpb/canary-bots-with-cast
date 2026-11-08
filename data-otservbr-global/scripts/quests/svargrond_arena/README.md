# Svargrond Arena

## Overview
Component package under `scripts/quests/svargrond_arena` containing 5 files (`creaturescripts_arena_kill.lua`..`movements_arena_trophy.lua`).

## Interface
- `deathEvent.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_arena_kill.lua:deathEvent.onDeath]
- `serverstartup.onStartup()` [creaturescripts_arena_kill.lua:serverstartup.onStartup]
- `CreatureEvent("SvargrondArenaBossDeath")` assigned to `deathEvent` [creaturescripts_arena_kill.lua:deathEvent]
- `CreatureEvent("SvargrondArenaBossDeath")` registration [creaturescripts_arena_kill.lua:CreatureEvent]
- `GlobalEvent("SvargrondArenaBossDeathStartup")` assigned to `serverstartup` [creaturescripts_arena_kill.lua:serverstartup]
- `GlobalEvent("SvargrondArenaBossDeathStartup")` registration [creaturescripts_arena_kill.lua:GlobalEvent]
- `svargrondArenaPlayerDeath.onDeath(player, corpse, killer, mostDamageKiller, unjustified, mostDamageUnjustified)` [creaturescripts_player_death.lua:svargrondArenaPlayerDeath.onDeath]
- `CreatureEvent("SvargrondArenaPlayerDeath")` assigned to `svargrondArenaPlayerDeath` [creaturescripts_player_death.lua:svargrondArenaPlayerDeath]
- `CreatureEvent("SvargrondArenaPlayerDeath")` registration [creaturescripts_player_death.lua:CreatureEvent]
- `arenaEnter.onStepIn(creature, item, position, fromPosition)` [movements_arena_enter.lua:arenaEnter.onStepIn]
- `MoveEvent()` assigned to `arenaEnter` [movements_arena_enter.lua:arenaEnter]
- `MoveEvent()` registration [movements_arena_enter.lua:MoveEvent]
- `arenaPit.onStepIn(creature, item, position, fromPosition)` [movements_arena_pit.lua:arenaPit.onStepIn]
- `MoveEvent()` assigned to `arenaPit` [movements_arena_pit.lua:arenaPit]
- `MoveEvent()` registration [movements_arena_pit.lua:MoveEvent]
- `arenaTrophy.onStepIn(creature, item, position, fromPosition)` [movements_arena_trophy.lua:arenaTrophy.onStepIn]
- `MoveEvent()` assigned to `arenaTrophy` [movements_arena_trophy.lua:arenaTrophy]
- `MoveEvent()` registration [movements_arena_trophy.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_arena_kill.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_arena_kill.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_player_death.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_arena_enter.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_arena_enter.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_arena_pit.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_arena_pit.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_arena_trophy.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_arena_trophy.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_arena_kill.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_arena_kill.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [creaturescripts_arena_kill.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [creaturescripts_arena_kill.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_player_death.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_player_death.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_arena_enter.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [movements_arena_enter.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_arena_enter.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_arena_pit.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_arena_pit.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [movements_arena_pit.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
