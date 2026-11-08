# The Inquisition Quest

## Overview
Component package under `scripts/quests/the_inquisition_quest` containing 9 files (`actions_brother_lever.lua`..`movements_teleport_main.lua`).

## Interface
- `inquisitionBrother.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_brother_lever.lua:inquisitionBrother.onUse]
- `Action()` assigned to `inquisitionBrother` [actions_brother_lever.lua:inquisitionBrother]
- `Action()` registration [actions_brother_lever.lua:Action]
- `inquisitionRewards.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_rewards.lua:inquisitionRewards.onUse]
- `Action()` assigned to `inquisitionRewards` [actions_rewards.lua:inquisitionRewards]
- `Action()` registration [actions_rewards.lua:Action]
- `inquisitionUngreez.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ungreez_door.lua:inquisitionUngreez.onUse]
- `Action()` assigned to `inquisitionUngreez` [actions_ungreez_door.lua:inquisitionUngreez]
- `Action()` registration [actions_ungreez_door.lua:Action]
- `inquisitionVampire.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_vampire_hunt.lua:inquisitionVampire.onUse]
- `Action()` assigned to `inquisitionVampire` [actions_vampire_hunt.lua:inquisitionVampire]
- `Action()` registration [actions_vampire_hunt.lua:Action]
- `inquisitionBossKill.onDeath(creature)` [creaturescripts_inquisition_boss.lua:inquisitionBossKill.onDeath]
- `CreatureEvent("InquisitionBossDeath")` assigned to `inquisitionBossKill` [creaturescripts_inquisition_boss.lua:inquisitionBossKill]
- `CreatureEvent("InquisitionBossDeath")` registration [creaturescripts_inquisition_boss.lua:CreatureEvent]
- `ungreezKill.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_inquisition_ungreez.lua:ungreezKill.onDeath]
- `CreatureEvent("UngreezDeath")` assigned to `ungreezKill` [creaturescripts_inquisition_ungreez.lua:ungreezKill]
- `CreatureEvent("UngreezDeath")` registration [creaturescripts_inquisition_ungreez.lua:CreatureEvent]
- `hasTouchedOneThrone(player)` [movements_entrance.lua:hasTouchedOneThrone]
- `entrance.onStepIn(creature, item, position, fromPosition)` [movements_entrance.lua:entrance.onStepIn]
- `MoveEvent()` assigned to `entrance` [movements_entrance.lua:entrance]
- `MoveEvent()` registration [movements_entrance.lua:MoveEvent]
- `rewardRoomText.onStepIn(creature, item, position, fromPosition)` [movements_reward_room_text.lua:rewardRoomText.onStepIn]
- `MoveEvent()` assigned to `rewardRoomText` [movements_reward_room_text.lua:rewardRoomText]
- `MoveEvent()` registration [movements_reward_room_text.lua:MoveEvent]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_brother_lever.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_rewards.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ungreez_door.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_vampire_hunt.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_vampire_hunt.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_inquisition_boss.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_inquisition_ungreez.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_entrance.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_entrance.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_reward_room_text.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_reward_room_text.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_teleport_main.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_brother_lever.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_brother_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_rewards.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_rewards.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_rewards.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ungreez_door.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_ungreez_door.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_ungreez_door.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_vampire_hunt.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_vampire_hunt.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_vampire_hunt.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_vampire_hunt.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
