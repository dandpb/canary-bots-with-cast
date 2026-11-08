# The Hidden City Of Beregar

## Overview
Component package under `scripts/quests/the_hidden_city_of_beregar` containing 12 files (`actions_bargate_lever.lua`..`moviments_tunnel.lua`).

## Interface
- `wall(i)` [actions_bargate_lever.lua:wall]
- `theHiddenBeregar.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bargate_lever.lua:theHiddenBeregar.onUse]
- `Action()` assigned to `theHiddenBeregar` [actions_bargate_lever.lua:theHiddenBeregar]
- `Action()` registration [actions_bargate_lever.lua:Action]
- `dwarvenLadder.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_ladder.lua:dwarvenLadder.onUse]
- `Action()` assigned to `dwarvenLadder` [actions_ladder.lua:dwarvenLadder]
- `Action()` registration [actions_ladder.lua:Action]
- `theHiddenWagonLevers.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_levers.lua:theHiddenWagonLevers.onUse]
- `Action()` assigned to `theHiddenWagonLevers` [actions_levers.lua:theHiddenWagonLevers]
- `Action()` registration [actions_levers.lua:Action]
- `wagons.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ore_wagon.lua:wagons.onUse]
- `Action()` assigned to `wagons` [actions_ore_wagon.lua:wagons]
- `Action()` registration [actions_ore_wagon.lua:Action]
- `firewalkerBootsKill.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_pythius_the_rotten_kill.lua:firewalkerBootsKill.onDeath]
- `CreatureEvent("PythiusTheRottenDeath")` assigned to `firewalkerBootsKill` [creaturescripts_pythius_the_rotten_kill.lua:firewalkerBootsKill]
- `CreatureEvent("PythiusTheRottenDeath")` registration [creaturescripts_pythius_the_rotten_kill.lua:CreatureEvent]
- `bellow.onStepIn(creature, item, position, fromPosition)` [moviments_bellow.lua:bellow.onStepIn]
- `bellow.onStepOut(creature, item, position, fromPosition)` [moviments_bellow.lua:bellow.onStepOut]
- `MoveEvent()` assigned to `bellow` [moviments_bellow.lua:bellow]
- `MoveEvent()` registration [moviments_bellow.lua:MoveEvent]
- `elevator.onStepIn(creature, item, position, fromPosition)` [moviments_elevator.lua:elevator.onStepIn]
- `MoveEvent()` assigned to `elevator` [moviments_elevator.lua:elevator]
- `MoveEvent()` registration [moviments_elevator.lua:MoveEvent]
- `gap.onStepIn(creature, item, position, fromPosition)` [moviments_gap.lua:gap.onStepIn]
- `MoveEvent()` assigned to `gap` [moviments_gap.lua:gap]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_bargate_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ladder.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_levers.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ore_wagon.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_ore_wagon.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [moviments_bellow.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [moviments_bellow.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [moviments_elevator.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [moviments_elevator.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [moviments_gap.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [moviments_ore_wagon.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [moviments_ore_wagon.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bargate_lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_bargate_lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bargate_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ladder.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_ladder.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_levers.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_levers.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_levers.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ore_wagon.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_ore_wagon.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_ore_wagon.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_ore_wagon.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
