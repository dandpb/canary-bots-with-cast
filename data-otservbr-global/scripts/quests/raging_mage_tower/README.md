# Raging Mage Tower

## Overview
Component package under `scripts/quests/raging_mage_tower` containing 5 files (`creaturescripts_energized_raging_mage_kill.lua`..`creaturescripts_yielothax_kill.lua`).

## Interface
- `deathEvent.onDeath(creature)` [creaturescripts_energized_raging_mage_kill.lua:deathEvent.onDeath]
- `CreatureEvent("EnergizedRagingMageDeath")` assigned to `deathEvent` [creaturescripts_energized_raging_mage_kill.lua:deathEvent]
- `CreatureEvent("EnergizedRagingMageDeath")` registration [creaturescripts_energized_raging_mage_kill.lua:CreatureEvent]
- `ragingMage1.onDeath(creature, corpse, killer, mostDamageKiller, unjustified, mostDamageUnjustified)` [creaturescripts_raging_mage_1.lua:ragingMage1.onDeath]
- `CreatureEvent("RagingMage1")` assigned to `ragingMage1` [creaturescripts_raging_mage_1.lua:ragingMage1]
- `CreatureEvent("RagingMage1")` registration [creaturescripts_raging_mage_1.lua:CreatureEvent]
- `ragingMage2.onDeath(creature, corpse, killer, mostDamageKiller, unjustified, mostDamageUnjustified)` [creaturescripts_raging_mage_2.lua:ragingMage2.onDeath]
- `CreatureEvent("RagingMage2")` assigned to `ragingMage2` [creaturescripts_raging_mage_2.lua:ragingMage2]
- `CreatureEvent("RagingMage2")` registration [creaturescripts_raging_mage_2.lua:CreatureEvent]
- `deathEvent.onDeath(creature)` [creaturescripts_raging_mage_kill.lua:deathEvent.onDeath]
- `CreatureEvent("RagingMageDeath")` assigned to `deathEvent` [creaturescripts_raging_mage_kill.lua:deathEvent]
- `CreatureEvent("RagingMageDeath")` registration [creaturescripts_raging_mage_kill.lua:CreatureEvent]
- `yielothaxKill.onDeath(creature)` [creaturescripts_yielothax_kill.lua:yielothaxKill.onDeath]
- `CreatureEvent("YielothaxDeath")` assigned to `yielothaxKill` [creaturescripts_yielothax_kill.lua:yielothaxKill]
- `CreatureEvent("YielothaxDeath")` registration [creaturescripts_yielothax_kill.lua:CreatureEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_raging_mage_1.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creaturescripts_raging_mage_1.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_raging_mage_2.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_raging_mage_kill.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_energized_raging_mage_kill.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [creaturescripts_energized_raging_mage_kill.lua:Game]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_raging_mage_1.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_raging_mage_1.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [creaturescripts_raging_mage_1.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [creaturescripts_raging_mage_1.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_raging_mage_2.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_raging_mage_2.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [creaturescripts_raging_mage_2.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [creaturescripts_raging_mage_2.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_raging_mage_kill.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [creaturescripts_raging_mage_kill.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
