# Dark Trails

## Overview
Component package under `scripts/quests/dark_trails` containing 7 files (`actions_corpse.lua`..`movements_necrometer_tile_access.lua`).

## Interface
- `darkCorpse.onUse(player)` [actions_corpse.lua:darkCorpse.onUse]
- `Action()` assigned to `darkCorpse` [actions_corpse.lua:darkCorpse]
- `Action()` registration [actions_corpse.lua:Action]
- `leverDeathPriestShargon.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lever_death_priest_shargon.lua:leverDeathPriestShargon.onUse]
- `Action()` assigned to `leverDeathPriestShargon` [actions_lever_death_priest_shargon.lua:leverDeathPriestShargon]
- `Action()` registration [actions_lever_death_priest_shargon.lua:Action]
- `leverTheRavager.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lever_the_ravager.lua:leverTheRavager.onUse]
- `Action()` assigned to `leverTheRavager` [actions_lever_the_ravager.lua:leverTheRavager]
- `Action()` registration [actions_lever_the_ravager.lua:Action]
- `removeTeleport(position)` [creaturescripts_kill_death_priest_shargon.lua:removeTeleport]
- `deathPriestShargon.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_kill_death_priest_shargon.lua:deathPriestShargon.onDeath]
- `CreatureEvent("DeathPriestShargonDeath")` assigned to `deathPriestShargon` [creaturescripts_kill_death_priest_shargon.lua:deathPriestShargon]
- `CreatureEvent("DeathPriestShargonDeath")` registration [creaturescripts_kill_death_priest_shargon.lua:CreatureEvent]
- `removeTeleport(position)` [creaturescripts_kill_the_ravager.lua:removeTeleport]
- `theRavager.onDeath(creature)` [creaturescripts_kill_the_ravager.lua:theRavager.onDeath]
- `CreatureEvent("TheRavagerDeath")` assigned to `theRavager` [creaturescripts_kill_the_ravager.lua:theRavager]
- `CreatureEvent("TheRavagerDeath")` registration [creaturescripts_kill_the_ravager.lua:CreatureEvent]
- `theRavagerHeal.onThink(creature)` [creaturescripts_think_the_ravager_heal.lua:theRavagerHeal.onThink]
- `CreatureEvent("TheRavagerHeal")` assigned to `theRavagerHeal` [creaturescripts_think_the_ravager_heal.lua:theRavagerHeal]
- `CreatureEvent("TheRavagerHeal")` registration [creaturescripts_think_the_ravager_heal.lua:CreatureEvent]
- `necrometerTileAccess.onStepIn(creature, item, position, fromPosition)` [movements_necrometer_tile_access.lua:necrometerTileAccess.onStepIn]
- `MoveEvent()` assigned to `necrometerTileAccess` [movements_necrometer_tile_access.lua:necrometerTileAccess]
- `MoveEvent()` registration [movements_necrometer_tile_access.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_corpse.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_lever_death_priest_shargon.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_lever_death_priest_shargon.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_lever_the_ravager.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_lever_the_ravager.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_kill_death_priest_shargon.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_kill_death_priest_shargon.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_kill_the_ravager.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_kill_the_ravager.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_think_the_ravager_heal.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_necrometer_tile_access.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_necrometer_tile_access.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_corpse.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_corpse.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lever_death_priest_shargon.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_lever_death_priest_shargon.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_lever_death_priest_shargon.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_lever_death_priest_shargon.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lever_the_ravager.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_lever_the_ravager.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_lever_the_ravager.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_lever_the_ravager.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_kill_death_priest_shargon.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_kill_death_priest_shargon.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
