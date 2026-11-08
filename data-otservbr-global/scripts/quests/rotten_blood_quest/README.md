# Rotten Blood Quest

## Overview
Component package under `scripts/quests/rotten_blood_quest` containing 9 files (`actions_bakragore_lever.lua`..`movements_blood_entrance.lua`).

## Interface
- `BossLever(config)` assigned to `lever` [actions_bakragore_lever.lua:lever]
- `BossLever(config)` registration [actions_bakragore_lever.lua:BossLever]
- `BossLever(config)` assigned to `lever` [actions_chagorz_lever.lua:lever]
- `BossLever(config)` registration [actions_chagorz_lever.lua:BossLever]
- `teleportEvent.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_entrances.lua:teleportEvent.onUse]
- `bakragoreEntrance.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_entrances.lua:bakragoreEntrance.onUse]
- `Action()` assigned to `teleportEvent` [actions_entrances.lua:teleportEvent]
- `Action()` assigned to `bakragoreEntrance` [actions_entrances.lua:bakragoreEntrance]
- `Action()` registration [actions_entrances.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_ichgahal_lever.lua:lever]
- `BossLever(config)` registration [actions_ichgahal_lever.lua:BossLever]
- `BossLever(config)` assigned to `lever` [actions_murcion_lever.lua:lever]
- `BossLever(config)` registration [actions_murcion_lever.lua:BossLever]
- `sacrificialPlate.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_sacrifice.lua:sacrificialPlate.onUse]
- `Action()` assigned to `sacrificialPlate` [actions_sacrifice.lua:sacrificialPlate]
- `Action()` registration [actions_sacrifice.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_vemiath_lever.lua:lever]
- `BossLever(config)` registration [actions_vemiath_lever.lua:BossLever]
- `bossesRottenBlood.onDeath(creature)` [creaturescripts_bosses_killed.lua:bossesRottenBlood.onDeath]
- `bakragoreOnDeath.onDeath(creature)` [creaturescripts_bosses_killed.lua:bakragoreOnDeath.onDeath]
- `CreatureEvent("RottenBloodBossDeath")` assigned to `bossesRottenBlood` [creaturescripts_bosses_killed.lua:bossesRottenBlood]
- `CreatureEvent("RottenBloodBakragoreDeath")` assigned to `bakragoreOnDeath` [creaturescripts_bosses_killed.lua:bakragoreOnDeath]
- `CreatureEvent("RottenBloodBossDeath")` registration [creaturescripts_bosses_killed.lua:CreatureEvent]
- `CreatureEvent("RottenBloodBakragoreDeath")` registration [creaturescripts_bosses_killed.lua:CreatureEvent]
- `getDamage(currentHealth)` [movements_blood_entrance.lua:getDamage]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_blood_entrance.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bakragore_lever.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_chagorz_lever.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_entrances.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_entrances.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ichgahal_lever.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_murcion_lever.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_sacrifice.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_sacrifice.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_vemiath_lever.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_bosses_killed.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_blood_entrance.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_blood_entrance.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
