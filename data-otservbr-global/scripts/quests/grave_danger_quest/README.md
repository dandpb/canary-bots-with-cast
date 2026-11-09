# Grave Danger Quest

## Overview
Provides 21 direct files (`actions_baeloc_nictros.lua`..`movements_zelos_tp.lua`) and 1 subdirectories under `scripts/quests/grave_danger_quest`.

## Interface
- `BossHealthCheck.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)` [actions_baeloc_nictros.lua:BossHealthCheck.onHealthChange]
- `getHealthPercentage(creature)` [actions_baeloc_nictros.lua:getHealthPercentage]
- `CreatureEvent("BossHealthCheck")` assigned to `BossHealthCheck` [actions_baeloc_nictros.lua:BossHealthCheck]
- `CreatureEvent("BossHealthCheck")` registration [actions_baeloc_nictros.lua:CreatureEvent]
- `BossLever(config)` assigned to `lever` [actions_baeloc_nictros.lua:lever]
- `BossLever(config)` registration [actions_baeloc_nictros.lua:BossLever]
- `BossLever(config)` assigned to `lever` [actions_count_vlarkorth_.lua:lever]
- `BossLever(config)` registration [actions_count_vlarkorth_.lua:BossLever]
- `custodian_door.onUse(player, item, isHotkey)` [actions_custodian_door.lua:custodian_door.onUse]
- `Action()` assigned to `custodian_door` [actions_custodian_door.lua:custodian_door]
- `Action()` registration [actions_custodian_door.lua:Action]
- `dark_remains.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_dark_remains.lua:dark_remains.onUse]
- `Action()` assigned to `dark_remains` [actions_dark_remains.lua:dark_remains]
- `Action()` registration [actions_dark_remains.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_duke_krule.lua:lever]
- `BossLever(config)` registration [actions_duke_krule.lua:BossLever]
- `BossLever(config)` assigned to `lever` [actions_earl_osam.lua:lever]
- `BossLever(config)` registration [actions_earl_osam.lua:BossLever]
- `getGrave(pos)` [actions_grave_sanctify.lua:getGrave]
- `grave_sanctify.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_grave_sanctify.lua:grave_sanctify.onUse]
- `Action()` assigned to `grave_sanctify` [actions_grave_sanctify.lua:grave_sanctify]
- `Action()` registration [actions_grave_sanctify.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_king_zelos.lua:lever]
- `BossLever(config)` registration [actions_king_zelos.lua:BossLever]
- `BossLever(config)` assigned to `lever` [actions_lord_azaram.lua:lever]
- [cobra_bastion](./cobra_bastion/README.md) - Component package under `scripts/quests/grave_danger_quest/cobra_bastion` containing 3 files (`actions_scarlett.lua`..`creaturescripts_ugly_monster.lua`).

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_custodian_door.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_dark_remains.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_dark_remains.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_grave_sanctify.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_boss_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_count_vlarkorth.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creaturescripts_count_vlarkorth.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_earl_osam.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creaturescripts_earl_osam.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_earl_osam.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_king_zelos.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creaturescripts_king_zelos.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_baeloc_nictros.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_baeloc_nictros.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_baeloc_nictros.lua:teleportTo]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_baeloc_nictros.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_count_vlarkorth_.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_custodian_door.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_custodian_door.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_dark_remains.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_dark_remains.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_dark_remains.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_duke_krule.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_earl_osam.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
