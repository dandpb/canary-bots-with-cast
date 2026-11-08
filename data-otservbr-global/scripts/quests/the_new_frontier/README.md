# The New Frontier

## Overview
Component package under `scripts/quests/the_new_frontier` containing 15 files (`action_arena.lua`..`movements_snake_head_teleport.lua`).

## Interface
- `summonBoss(name, position)` [action_arena.lua:summonBoss]
- `clearArena()` [action_arena.lua:clearArena]
- `theNewFrontierArena.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_arena.lua:theNewFrontierArena.onUse]
- `Action()` assigned to `theNewFrontierArena` [action_arena.lua:theNewFrontierArena]
- `Action()` registration [action_arena.lua:Action]
- `beaverTrees.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_beaver.lua:beaverTrees.onUse]
- `Action()` assigned to `beaverTrees` [action_beaver.lua:beaverTrees]
- `Action()` registration [action_beaver.lua:Action]
- `farmineElevatorLevers.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_elevator.lua:farmineElevatorLevers.onUse]
- `Action()` assigned to `farmineElevatorLevers` [action_elevator.lua:farmineElevatorLevers]
- `Action()` registration [action_elevator.lua:Action]
- `hiddenNote.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_hidden_note.lua:hiddenNote.onUse]
- `Action()` assigned to `hiddenNote` [action_hidden_note.lua:hiddenNote]
- `Action()` registration [action_hidden_note.lua:Action]
- `theNewFrontierOutfit.onUse(player, item)` [action_outfit.lua:theNewFrontierOutfit.onUse]
- `Action()` assigned to `theNewFrontierOutfit` [action_outfit.lua:theNewFrontierOutfit]
- `Action()` registration [action_outfit.lua:Action]
- `prisionSecretDoor.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_prision_secret_door.lua:prisionSecretDoor.onUse]
- `Action()` assigned to `prisionSecretDoor` [action_prision_secret_door.lua:prisionSecretDoor]
- `Action()` registration [action_prision_secret_door.lua:Action]
- `theNewFrontierVine.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_vine.lua:theNewFrontierVine.onUse]
- `Action()` assigned to `theNewFrontierVine` [action_vine.lua:theNewFrontierVine]
- `Action()` registration [action_vine.lua:Action]
- `shardOfCorruptionKill.onDeath(creature)` [creaturescripts_shard_of_corruption_kill.lua:shardOfCorruptionKill.onDeath]
- `CreatureEvent("ShardOfCorruptionDeath")` assigned to `shardOfCorruptionKill` [creaturescripts_shard_of_corruption_kill.lua:shardOfCorruptionKill]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_arena.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [action_arena.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action_arena.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_beaver.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_elevator.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_hidden_note.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_outfit.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_prision_secret_door.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_shard_of_corruption_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_tirecz_kill.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creaturescripts_tirecz_kill.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movement_corruption_hole.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_arena.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_arena.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [action_arena.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [action_arena.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_arena.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [action_arena.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_beaver.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_beaver.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [action_beaver.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_beaver.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_elevator.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [action_elevator.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
