# The First Dragon

## Overview
Component package under `scripts/quests/the_first_dragon` containing 17 files (`actions_lair_entrance.lua`..`movements_zorvorax_secrets.lua`).

## Interface
- `lairEntrance.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lair_entrance.lua:lairEntrance.onUse]
- `Action()` assigned to `lairEntrance` [actions_lair_entrance.lua:lairEntrance]
- `Action()` registration [actions_lair_entrance.lua:Action]
- `BossLever(config)` assigned to `leverFirstDragon` [actions_lever.lua:leverFirstDragon]
- `BossLever(config)` registration [actions_lever.lua:BossLever]
- `finalReward.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_rewards.lua:finalReward.onUse]
- `Action()` assigned to `finalReward` [actions_rewards.lua:finalReward]
- `Action()` registration [actions_rewards.lua:Action]
- `sacrificeItems.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_sacrifice_items.lua:sacrificeItems.onUse]
- `Action()` assigned to `sacrificeItems` [actions_sacrifice_items.lua:sacrificeItems]
- `Action()` registration [actions_sacrifice_items.lua:Action]
- `treasureChest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_treasure_chest.lua:treasureChest.onUse]
- `Action()` assigned to `treasureChest` [actions_treasure_chest.lua:treasureChest]
- `Action()` registration [actions_treasure_chest.lua:Action]
- `deathAngryPlant.onDeath(creature, corpse, lasthitkiller, mostdamagekiller, lasthitunjustified, mostdamageunjustified)` [creaturescripts_death_angry_plant.lua:deathAngryPlant.onDeath]
- `CreatureEvent("AngryPlantDeath")` assigned to `deathAngryPlant` [creaturescripts_death_angry_plant.lua:deathAngryPlant]
- `CreatureEvent("AngryPlantDeath")` registration [creaturescripts_death_angry_plant.lua:CreatureEvent]
- `deathDragonEssence.onDeath(creature, corpse, lasthitkiller, mostdamagekiller, lasthitunjustified, mostdamageunjustified)` [creaturescripts_death_dragon_essence.lua:deathDragonEssence.onDeath]
- `CreatureEvent("DragonEssenceDeath")` assigned to `deathDragonEssence` [creaturescripts_death_dragon_essence.lua:deathDragonEssence]
- `CreatureEvent("DragonEssenceDeath")` registration [creaturescripts_death_dragon_essence.lua:CreatureEvent]
- `removeTp(position, itemid)` [creaturescripts_death_fallen.lua:removeTp]
- `deathFallen.onDeath(creature, corpse, lasthitkiller, mostdamagekiller, lasthitunjustified, mostdamageunjustified)` [creaturescripts_death_fallen.lua:deathFallen.onDeath]
- `CreatureEvent("FallenDeath")` assigned to `deathFallen` [creaturescripts_death_fallen.lua:deathFallen]
- `CreatureEvent("FallenDeath")` registration [creaturescripts_death_fallen.lua:CreatureEvent]
- `deathFirstDragon.onDeath(creature, corpse, lasthitkiller, mostdamagekiller, lasthitunjustified, mostdamageunjustified)` [creaturescripts_death_first_dragon.lua:deathFirstDragon.onDeath]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lair_entrance.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_lever.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_rewards.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_sacrifice_items.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_sacrifice_items.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_treasure_chest.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_death_fallen.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_death_first_dragon.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creaturescripts_death_first_dragon.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_death_somewhat_beatable.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creaturescripts_death_somewhat_beatable.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_kill_dragon.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lair_entrance.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_lair_entrance.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lever.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_lever.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_rewards.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_rewards.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_rewards.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_rewards.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_sacrifice_items.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_sacrifice_items.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_sacrifice_items.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_treasure_chest.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
