# Primal Ordeal Quest

## Overview
Component package under `scripts/quests/primal_ordeal_quest` containing 5 files (`bosses_killed.lua`..`the_primal_menace.lua`).

## Interface
- `bossesPrimeOrdeal.onDeath(creature)` [bosses_killed.lua:bossesPrimeOrdeal.onDeath]
- `CreatureEvent("ThePrimeOrdealBossDeath")` assigned to `bossesPrimeOrdeal` [bosses_killed.lua:bossesPrimeOrdeal]
- `CreatureEvent("ThePrimeOrdealBossDeath")` registration [bosses_killed.lua:CreatureEvent]
- `BossLever(config)` assigned to `lever` [magma_bubble.lua:lever]
- `BossLever(config)` registration [magma_bubble.lua:BossLever]
- `encounter:onReset(position)` [magma_bubble_fight.lua:encounter:onReset]
- `addShieldStack(player)` [magma_bubble_fight.lua:addShieldStack]
- `tickShields(player)` [magma_bubble_fight.lua:tickShields]
- `overheatedDamage.onThink(interval, lastExecution)` [magma_bubble_fight.lua:overheatedDamage.onThink]
- `crystalsCycle.onThink(interval, lastExecution)` [magma_bubble_fight.lua:crystalsCycle.onThink]
- `randomPosition(positions)` [magma_bubble_fight.lua:randomPosition]
- `chargedFlameAction.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [magma_bubble_fight.lua:chargedFlameAction.onUse]
- `shieldField.onStepIn(creature, item, position, fromPosition)` [magma_bubble_fight.lua:shieldField.onStepIn]
- `theEndOfDaysHealth.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType)` [magma_bubble_fight.lua:theEndOfDaysHealth.onHealthChange]
- `magmaCrystalDeath.onDeath()` [magma_bubble_fight.lua:magmaCrystalDeath.onDeath]
- `endOfDaysDeath.onDeath()` [magma_bubble_fight.lua:endOfDaysDeath.onDeath]
- `magmaBubbleDeath.onDeath()` [magma_bubble_fight.lua:magmaBubbleDeath.onDeath]
- `zoneEvent.afterEnter(_zone, creature)` [magma_bubble_fight.lua:zoneEvent.afterEnter]
- `zoneEvent.afterLeave(_zone, creature)` [magma_bubble_fight.lua:zoneEvent.afterLeave]
- `Action()` assigned to `chargedFlameAction` [magma_bubble_fight.lua:chargedFlameAction]
- `Action()` registration [magma_bubble_fight.lua:Action]
- `MoveEvent()` assigned to `shieldField` [magma_bubble_fight.lua:shieldField]
- `MoveEvent()` registration [magma_bubble_fight.lua:MoveEvent]
- `CreatureEvent("fight.magma-bubble.TheEndOfDaysHealth")` assigned to `theEndOfDaysHealth` [magma_bubble_fight.lua:theEndOfDaysHealth]
- `CreatureEvent("fight.magma-bubble.MagmaCrystalDeath")` assigned to `magmaCrystalDeath` [magma_bubble_fight.lua:magmaCrystalDeath]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [magma_bubble_fight.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [magma_bubble_fight.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [bosses_killed.lua:register]
- Mutates player or global storage state via `setStorageValue` [bosses_killed.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [magma_bubble.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [magma_bubble_fight.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [magma_bubble_fight.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [magma_bubble_fight.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [magma_bubble_fight.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [ore_wagons_gnoproma.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [ore_wagons_gnoproma.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [the_primal_menace.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
