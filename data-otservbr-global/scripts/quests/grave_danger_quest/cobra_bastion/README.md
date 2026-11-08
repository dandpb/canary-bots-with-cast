# Cobra Bastion

## Overview
Component package under `scripts/quests/grave_danger_quest/cobra_bastion` containing 3 files (`actions_scarlett.lua`..`creaturescripts_ugly_monster.lua`).

## Interface
- `createArmor(id, amount, pos)` [actions_scarlett.lua:createArmor]
- `backMirror()` [actions_scarlett.lua:backMirror]
- `graveScarlettAid.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_scarlett.lua:graveScarlettAid.onUse]
- `Action()` assigned to `graveScarlettAid` [actions_scarlett.lua:graveScarlettAid]
- `Action()` registration [actions_scarlett.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_scarlett.lua:lever]
- `BossLever(config)` registration [actions_scarlett.lua:BossLever]
- `onTargetCreature(creature, target)` [creaturescripts_scarlett.lua:onTargetCreature]
- `isMirrorsCorrect(fromPosition, toPosition)` [creaturescripts_scarlett.lua:isMirrorsCorrect]
- `changeScarlett(creatureid)` [creaturescripts_scarlett.lua:changeScarlett]
- `scarlettThink.onThink(creature)` [creaturescripts_scarlett.lua:scarlettThink.onThink]
- `scarlettHealth.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)` [creaturescripts_scarlett.lua:scarlettHealth.onHealthChange]
- `CreatureEvent("scarlettThink")` assigned to `scarlettThink` [creaturescripts_scarlett.lua:scarlettThink]
- `CreatureEvent("scarlettHealth")` assigned to `scarlettHealth` [creaturescripts_scarlett.lua:scarlettHealth]
- `CreatureEvent("scarlettThink")` registration [creaturescripts_scarlett.lua:CreatureEvent]
- `CreatureEvent("scarlettHealth")` registration [creaturescripts_scarlett.lua:CreatureEvent]
- `uglyMonsterSpawn.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)` [creaturescripts_ugly_monster.lua:uglyMonsterSpawn.onHealthChange]
- `uglyMonsterCleanup.onDeath(creature, corpse, killer, mostDamage, unjustified, mostDamage_unjustified)` [creaturescripts_ugly_monster.lua:uglyMonsterCleanup.onDeath]
- `uglyMonsterDeath.onDeath(creature, corpse, killer, mostDamage, unjustified, mostDamage_unjustified)` [creaturescripts_ugly_monster.lua:uglyMonsterDeath.onDeath]
- `uglyMonsterDrop.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)` [creaturescripts_ugly_monster.lua:uglyMonsterDrop.onHealthChange]
- `CreatureEvent("UglyMonsterSpawn")` assigned to `uglyMonsterSpawn` [creaturescripts_ugly_monster.lua:uglyMonsterSpawn]
- `CreatureEvent("UglyMonsterCleanup")` assigned to `uglyMonsterCleanup` [creaturescripts_ugly_monster.lua:uglyMonsterCleanup]
- `CreatureEvent("UglyMonsterDeath")` assigned to `uglyMonsterDeath` [creaturescripts_ugly_monster.lua:uglyMonsterDeath]
- `CreatureEvent("UglyMonsterDrop")` assigned to `uglyMonsterDrop` [creaturescripts_ugly_monster.lua:uglyMonsterDrop]
- `CreatureEvent("UglyMonsterSpawn")` registration [creaturescripts_ugly_monster.lua:CreatureEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_scarlett.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_scarlett.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_scarlett.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_scarlett.lua:Tile]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [creaturescripts_scarlett.lua:combat]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_ugly_monster.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_scarlett.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_scarlett.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_scarlett.lua:Game]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_scarlett.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_scarlett.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_scarlett.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_scarlett.lua:register]
- Executes combat damage, healing, or condition effects on targets via `combat:execute(creature, var)` [creaturescripts_scarlett.lua:combat:execute]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [creaturescripts_scarlett.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_ugly_monster.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_ugly_monster.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [creaturescripts_ugly_monster.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
