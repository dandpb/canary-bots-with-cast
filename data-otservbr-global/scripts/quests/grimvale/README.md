# Grimvale

## Overview
Component package under `scripts/quests/grimvale` containing 9 files (`actions_ancient_feud_entrances.lua`..`movements_strangely_glowing_mark.lua`).

## Interface
- `entranceAncientFeud.onUse(creature, item, position, fromPosition)` [actions_ancient_feud_entrances.lua:entranceAncientFeud.onUse]
- `Action()` assigned to `entranceAncientFeud` [actions_ancient_feud_entrances.lua:entranceAncientFeud]
- `Action()` registration [actions_ancient_feud_entrances.lua:Action]
- `grimValeClosed.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_closed_silvered_trap.lua:grimValeClosed.onUse]
- `Action()` assigned to `grimValeClosed` [actions_closed_silvered_trap.lua:grimValeClosed]
- `Action()` registration [actions_closed_silvered_trap.lua:Action]
- `teleportBoss.onStepIn(creature, item, position, fromPosition)` [actions_portal_minis_ancient_feud.lua:teleportBoss.onStepIn]
- `MoveEvent()` assigned to `teleportBoss` [actions_portal_minis_ancient_feud.lua:teleportBoss]
- `MoveEvent()` registration [actions_portal_minis_ancient_feud.lua:MoveEvent]
- `teleportBoss.onStepIn(creature, item, position, fromPosition)` [actions_portal_minis_grimvale.lua:teleportBoss.onStepIn]
- `MoveEvent()` assigned to `teleportBoss` [actions_portal_minis_grimvale.lua:teleportBoss]
- `MoveEvent()` registration [actions_portal_minis_grimvale.lua:MoveEvent]
- `grimValeSilver.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_silver_liquid.lua:grimValeSilver.onUse]
- `Action()` assigned to `grimValeSilver` [actions_silver_liquid.lua:grimValeSilver]
- `Action()` registration [actions_silver_liquid.lua:Action]
- `feroxaTransform.onThink(creature)` [creaturescripts_feroxa_transform.lua:feroxaTransform.onThink]
- `feroxaDeath.onDeath(creature, corpse, deathList)` [creaturescripts_feroxa_transform.lua:feroxaDeath.onDeath]
- `CreatureEvent("FeroxaTransform")` assigned to `feroxaTransform` [creaturescripts_feroxa_transform.lua:feroxaTransform]
- `CreatureEvent("FeroxaDeath")` assigned to `feroxaDeath` [creaturescripts_feroxa_transform.lua:feroxaDeath]
- `CreatureEvent("FeroxaTransform")` registration [creaturescripts_feroxa_transform.lua:CreatureEvent]
- `CreatureEvent("FeroxaDeath")` registration [creaturescripts_feroxa_transform.lua:CreatureEvent]
- `grimVale.onThink(interval, lastExecution)` [globalevents_grimvale_feroxa.lua:grimVale.onThink]
- `GlobalEvent("grimvale")` assigned to `grimVale` [globalevents_grimvale_feroxa.lua:grimVale]
- `GlobalEvent("grimvale")` registration [globalevents_grimvale_feroxa.lua:GlobalEvent]
- `silveredTrap.onStepIn(creature, item, position, fromPosition)` [movements_silvered_trap.lua:silveredTrap.onStepIn]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ancient_feud_entrances.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_ancient_feud_entrances.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_portal_minis_ancient_feud.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_portal_minis_ancient_feud.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_portal_minis_grimvale.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_portal_minis_grimvale.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_feroxa_transform.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [globalevents_grimvale_feroxa.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_strangely_glowing_mark.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_strangely_glowing_mark.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ancient_feud_entrances.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_ancient_feud_entrances.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_closed_silvered_trap.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_closed_silvered_trap.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_portal_minis_ancient_feud.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_portal_minis_ancient_feud.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_portal_minis_ancient_feud.lua:teleportTo]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_portal_minis_ancient_feud.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_portal_minis_grimvale.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_portal_minis_grimvale.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_portal_minis_grimvale.lua:teleportTo]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_portal_minis_grimvale.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
