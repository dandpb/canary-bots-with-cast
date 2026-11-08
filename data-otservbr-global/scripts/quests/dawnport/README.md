# Dawnport

## Overview
Component package under `scripts/quests/dawnport` containing 7 files (`actions_legion_helmet.lua`..`movements_legion_helmet.lua`).

## Interface
- `sacredSnake.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_legion_helmet.lua:sacredSnake.onUse]
- `Action()` assigned to `sacredSnake` [actions_legion_helmet.lua:sacredSnake]
- `Action()` registration [actions_legion_helmet.lua:Action]
- `theRareHerb.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_the_rare_herb.lua:theRareHerb.onUse]
- `Action()` assigned to `theRareHerb` [actions_the_rare_herb.lua:theRareHerb]
- `Action()` registration [actions_the_rare_herb.lua:Action]
- `vocationReward.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_vocation_reward.lua:vocationReward.onUse]
- `Action()` assigned to `vocationReward` [actions_vocation_reward.lua:vocationReward]
- `Action()` registration [actions_vocation_reward.lua:Action]
- `goblinKill.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_goblin_kill.lua:goblinKill.onDeath]
- `CreatureEvent("MorrisGoblinDeath")` assigned to `goblinKill` [creaturescripts_goblin_kill.lua:goblinKill]
- `CreatureEvent("MorrisGoblinDeath")` registration [creaturescripts_goblin_kill.lua:CreatureEvent]
- `minotaurKill.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_minotaur_kill.lua:minotaurKill.onDeath]
- `CreatureEvent("MorrisMinotaurDeath")` assigned to `minotaurKill` [creaturescripts_minotaur_kill.lua:minotaurKill]
- `CreatureEvent("MorrisMinotaurDeath")` registration [creaturescripts_minotaur_kill.lua:CreatureEvent]
- `trollKill.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_troll_kill.lua:trollKill.onDeath]
- `CreatureEvent("MorrisTrollDeath")` assigned to `trollKill` [creaturescripts_troll_kill.lua:trollKill]
- `CreatureEvent("MorrisTrollDeath")` registration [creaturescripts_troll_kill.lua:CreatureEvent]
- `sacrificeTeleport.onStepIn(creature, item, position, fromPosition)` [movements_legion_helmet.lua:sacrificeTeleport.onStepIn]
- `MoveEvent()` assigned to `sacrificeTeleport` [movements_legion_helmet.lua:sacrificeTeleport]
- `MoveEvent()` registration [movements_legion_helmet.lua:MoveEvent]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_legion_helmet.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_the_rare_herb.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_vocation_reward.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_goblin_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_minotaur_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_troll_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_legion_helmet.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_legion_helmet.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_legion_helmet.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_legion_helmet.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_the_rare_herb.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_the_rare_herb.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_vocation_reward.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_vocation_reward.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_vocation_reward.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_vocation_reward.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_goblin_kill.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_goblin_kill.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_minotaur_kill.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_minotaur_kill.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
