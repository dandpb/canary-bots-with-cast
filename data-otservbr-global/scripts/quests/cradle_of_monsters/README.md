# Cradle Of Monsters

## Overview
Component package under `scripts/quests/cradle_of_monsters` containing 2 files (`the_monster.lua`..`the_monster_fight.lua`).

## Interface
- `BossLever(config)` assigned to `lever` [the_monster.lua:lever]
- `BossLever(config)` registration [the_monster.lua:BossLever]
- `freeMonster()` [the_monster_fight.lua:freeMonster]
- `encounter:onReset(position)` [the_monster_fight.lua:encounter:onReset]
- `spawnContainers.onThink(interval, lastExecution)` [the_monster_fight.lua:spawnContainers.onThink]
- `doctorHealth.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType)` [the_monster_fight.lua:doctorHealth.onHealthChange]
- `antennaDeath.onDeath()` [the_monster_fight.lua:antennaDeath.onDeath]
- `alchemistContainerDeath.onDeath(creature)` [the_monster_fight.lua:alchemistContainerDeath.onDeath]
- `alchemistContainerSpawns.onThink()` [the_monster_fight.lua:alchemistContainerSpawns.onThink]
- `getShields(creature)` [the_monster_fight.lua:getShields]
- `setShields(creature, count)` [the_monster_fight.lua:setShields]
- `monsterHealth.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType)` [the_monster_fight.lua:monsterHealth.onHealthChange]
- `monsterDeath.onDeath(creature)` [the_monster_fight.lua:monsterDeath.onDeath]
- `puddleStepIn.onStepIn(creature, item, position, fromPosition)` [the_monster_fight.lua:puddleStepIn.onStepIn]
- `MoveEvent("fight.the-monster.PuddleStepIn")` assigned to `puddleStepIn` [the_monster_fight.lua:puddleStepIn]
- `MoveEvent("fight.the-monster.PuddleStepIn")` registration [the_monster_fight.lua:MoveEvent]
- `CreatureEvent("fight.the-monster.DoctorMarrowHealth")` assigned to `doctorHealth` [the_monster_fight.lua:doctorHealth]
- `CreatureEvent("fight.the-monster.AntennaDeath")` assigned to `antennaDeath` [the_monster_fight.lua:antennaDeath]
- `CreatureEvent("fight.the-monster.AlchemistContainerDeath")` assigned to `alchemistContainerDeath` [the_monster_fight.lua:alchemistContainerDeath]
- `CreatureEvent("fight.the-monster.TheMonsterHealth")` assigned to `monsterHealth` [the_monster_fight.lua:monsterHealth]
- `CreatureEvent("fight.the-monster.TheMonsterDeath")` assigned to `monsterDeath` [the_monster_fight.lua:monsterDeath]
- `CreatureEvent("fight.the-monster.DoctorMarrowHealth")` registration [the_monster_fight.lua:CreatureEvent]
- `CreatureEvent("fight.the-monster.AntennaDeath")` registration [the_monster_fight.lua:CreatureEvent]
- `CreatureEvent("fight.the-monster.AlchemistContainerDeath")` registration [the_monster_fight.lua:CreatureEvent]
- `CreatureEvent("fight.the-monster.TheMonsterHealth")` registration [the_monster_fight.lua:CreatureEvent]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [the_monster_fight.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [the_monster.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [the_monster_fight.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [the_monster_fight.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [the_monster_fight.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
