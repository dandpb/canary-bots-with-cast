# Their Masters Voice

## Overview
Component package under `scripts/quests/their_masters_voice` containing 5 files (`actions_slime_gobbler.lua`..`movements_entrance.lua`).

## Interface
- `slimeGobbler.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_slime_gobbler.lua:slimeGobbler.onUse]
- `Action()` assigned to `slimeGobbler` [actions_slime_gobbler.lua:slimeGobbler]
- `Action()` registration [actions_slime_gobbler.lua:Action]
- `mageDeath.onDeath(creature, corpse, killer, mostDamageKiller, lastHitUnjustified)` [creaturescripts_mage_death.lua:mageDeath.onDeath]
- `CreatureEvent("MageDeath")` assigned to `mageDeath` [creaturescripts_mage_death.lua:mageDeath]
- `CreatureEvent("MageDeath")` registration [creaturescripts_mage_death.lua:CreatureEvent]
- `servantDeath.onDeath(creature, corpse, killer, mostDamageKiller, lastHitUnjustified)` [creaturescripts_servant_death.lua:servantDeath.onDeath]
- `CreatureEvent("ServantDeath")` assigned to `servantDeath` [creaturescripts_servant_death.lua:servantDeath]
- `CreatureEvent("ServantDeath")` registration [creaturescripts_servant_death.lua:CreatureEvent]
- `mad.onThink(interval, lastExecution)` [globalevents_their_master_voice_mad_mage.lua:mad.onThink]
- `GlobalEvent("MadMage")` assigned to `mad` [globalevents_their_master_voice_mad_mage.lua:mad]
- `GlobalEvent("MadMage")` registration [globalevents_their_master_voice_mad_mage.lua:GlobalEvent]
- `entrance.onStepIn(creature, item, toPosition, fromPosition)` [movements_entrance.lua:entrance.onStepIn]
- `MoveEvent()` assigned to `entrance` [movements_entrance.lua:entrance]
- `MoveEvent()` registration [movements_entrance.lua:MoveEvent]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_slime_gobbler.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_mage_death.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_servant_death.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [globalevents_their_master_voice_mad_mage.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [globalevents_their_master_voice_mad_mage.lua:Game]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_entrance.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
