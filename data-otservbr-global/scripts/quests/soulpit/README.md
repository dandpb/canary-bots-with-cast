# Soulpit

## Overview
Component package under `scripts/quests/soulpit` containing 8 files (`exalted_core.lua`..`soulpit_powerless.lua`).

## Interface
- `getPreviousDifficultyLevel(currentLevel)` [exalted_core.lua:getPreviousDifficultyLevel]
- `getSoulCoreItemForMonster(monsterName)` [exalted_core.lua:getSoulCoreItemForMonster]
- `exaltedCore.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [exalted_core.lua:exaltedCore.onUse]
- `Action()` assigned to `exaltedCore` [exalted_core.lua:exaltedCore]
- `Action()` registration [exalted_core.lua:Action]
- `callback.monsterOnDropLoot(monster, corpse)` [ondroploot_soul_core.lua:callback.monsterOnDropLoot]
- `EventCallback("MonsterOnDropLootSoulCore")` assigned to `callback` [ondroploot_soul_core.lua:callback]
- `EventCallback("MonsterOnDropLootSoulCore")` registration [ondroploot_soul_core.lua:EventCallback]
- Exported Lua configuration table [ondroploot_soul_core.lua:return]
- `getNextDifficultyLevel(currentLevel)` [soul_prism.lua:getNextDifficultyLevel]
- `getPreviousDifficultyLevel(currentLevel)` [soul_prism.lua:getPreviousDifficultyLevel]
- `getSoulCoreItemForMonster(monsterName)` [soul_prism.lua:getSoulCoreItemForMonster]
- `soulPrism.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [soul_prism.lua:soulPrism.onUse]
- `Action()` assigned to `soulPrism` [soul_prism.lua:soulPrism]
- `Action()` registration [soul_prism.lua:Action]
- `enrage.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType)` [soulpit_creatureevents.lua:enrage.onHealthChange]
- `CreatureEvent("enrageSoulPit")` assigned to `enrage` [soulpit_creatureevents.lua:enrage]
- `CreatureEvent("enrageSoulPit")` registration [soulpit_creatureevents.lua:CreatureEvent]
- `zoneEvent.afterLeave(zone, creature)` [soulpit_fight.lua:zoneEvent.afterLeave]
- `soulPitAction.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [soulpit_fight.lua:soulPitAction.onUse]
- `encounter:onReset(position)` [soulpit_fight.lua:encounter:onReset]
- `waveStart()` [soulpit_fight.lua:waveStart]
- `Action()` assigned to `soulPitAction` [soulpit_fight.lua:soulPitAction]
- `Action()` registration [soulpit_fight.lua:Action]
- `Encounter("Soulpit", {
		zone = SoulPit.zone,
	})` assigned to `encounter` [soulpit_fight.lua:encounter]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [soulpit_fight.lua:getPlayer]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [soulpit_intensehex.lua:combat]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [soulpit_powerless.lua:combat]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [exalted_core.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [exalted_core.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [ondroploot_soul_core.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [soul_prism.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [soul_prism.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [soulpit_creatureevents.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [soulpit_fight.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [soulpit_fight.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [soulpit_fight.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [soulpit_intensehex.lua:register]
- Executes combat damage, healing, or condition effects on targets via `combat:execute(creature, var)` [soulpit_intensehex.lua:combat:execute]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [soulpit_opressor.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
