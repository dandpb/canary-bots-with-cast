# Feaster Of Souls

## Overview
Component package under `scripts/quests/feaster_of_souls` containing 14 files (`actions_bosses_killed.lua`..`creaturescripts_wormling_death.lua`).

## Interface
- `bossesFeasterOfSouls.onDeath(creature)` [actions_bosses_killed.lua:bossesFeasterOfSouls.onDeath]
- `CreatureEvent("FeasterOfSoulsBossDeath")` assigned to `bossesFeasterOfSouls` [actions_bosses_killed.lua:bossesFeasterOfSouls]
- `CreatureEvent("FeasterOfSoulsBossDeath")` registration [actions_bosses_killed.lua:CreatureEvent]
- `feasterEntrances.onStepIn(creature, item, position, fromPosition)` [actions_entrances.lua:feasterEntrances.onStepIn]
- `MoveEvent()` assigned to `feasterEntrances` [actions_entrances.lua:feasterEntrances]
- `MoveEvent()` registration [actions_entrances.lua:MoveEvent]
- `encounter:onReset()` [actions_portal_brain_head.lua:encounter:onReset]
- `teleportBoss.onStepIn(creature, item, position, fromPosition)` [actions_portal_brain_head.lua:teleportBoss.onStepIn]
- `MoveEvent()` assigned to `teleportBoss` [actions_portal_brain_head.lua:teleportBoss]
- `MoveEvent()` registration [actions_portal_brain_head.lua:MoveEvent]
- `Encounter("Brain Head", {
	zone = zone,
	timeToSpawnMonsters = "50ms",
})` assigned to `encounter` [actions_portal_brain_head.lua:encounter]
- `Encounter("Brain Head", {
	zone = zone,
	timeToSpawnMonsters = "50ms",
})` registration [actions_portal_brain_head.lua:Encounter]
- `Zone("boss." .. toKey(config.bossName)` assigned to `zone` [actions_portal_brain_head.lua:zone]
- `Zone("boss." .. toKey(config.bossName)` registration [actions_portal_brain_head.lua:Zone]
- `teleportBoss.onStepIn(creature, item, position, fromPosition)` [actions_portal_minis_feaster.lua:teleportBoss.onStepIn]
- `MoveEvent()` assigned to `teleportBoss` [actions_portal_minis_feaster.lua:teleportBoss]
- `MoveEvent()` registration [actions_portal_minis_feaster.lua:MoveEvent]
- `portalPaleWorm.onStepIn(creature, item, position, fromPosition)` [actions_portal_pale_worm.lua:portalPaleWorm.onStepIn]
- `MoveEvent()` assigned to `portalPaleWorm` [actions_portal_pale_worm.lua:portalPaleWorm]
- `MoveEvent()` registration [actions_portal_pale_worm.lua:MoveEvent]
- `feasterrocks.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_rock_entrance.lua:feasterrocks.onUse]
- `Action()` assigned to `feasterrocks` [actions_rock_entrance.lua:feasterrocks]
- `Action()` registration [actions_rock_entrance.lua:Action]
- `slab.onStepIn(creature, item, position, fromPosition)` [actions_slab.lua:slab.onStepIn]
- `MoveEvent()` assigned to `slab` [actions_slab.lua:slab]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_entrances.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_entrances.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_portal_brain_head.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_portal_minis_feaster.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_portal_minis_feaster.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_portal_pale_worm.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_portal_pale_worm.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_slab.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_brother_worm_death.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_pale_worm_death.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creaturescripts_pale_worm_death.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creaturescripts_wormling_death.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bosses_killed.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_bosses_killed.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_entrances.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_entrances.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_portal_brain_head.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_portal_brain_head.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_portal_minis_feaster.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_portal_minis_feaster.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_portal_minis_feaster.lua:teleportTo]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_portal_minis_feaster.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_portal_pale_worm.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_portal_pale_worm.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
