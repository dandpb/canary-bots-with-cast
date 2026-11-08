# A Pirates Tail

## Overview
Component package under `scripts/quests/a_pirates_tail` containing 7 files (`actions_cheesy_key.lua`..`creaturescripts_tentugly_death.lua`).

## Interface
- `action.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_cheesy_key.lua:action.onUse]
- `Action()` assigned to `action` [actions_cheesy_key.lua:action]
- `Action()` registration [actions_cheesy_key.lua:Action]
- `rascacoonShortcut.onUse(creature, item, position, fromPosition)` [actions_rascacoon_shortcut.lua:rascacoonShortcut.onUse]
- `Action()` assigned to `rascacoonShortcut` [actions_rascacoon_shortcut.lua:rascacoonShortcut]
- `Action()` registration [actions_rascacoon_shortcut.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_ratmiral_blackwhiskers.lua:lever]
- `BossLever(config)` registration [actions_ratmiral_blackwhiskers.lua:BossLever]
- `BossLever(config)` assigned to `lever` [actions_tentuglys_head.lua:lever]
- `BossLever(config)` registration [actions_tentuglys_head.lua:BossLever]
- `tentuglysHeadDeath.onDeath(creature, corpse, killer, mostDamage, unjustified, mostDamage_unjustified)` [creaturescripts_a_pirates_tail_bosses.lua:tentuglysHeadDeath.onDeath]
- `CreatureEvent("TentuglysHeadDeath")` assigned to `tentuglysHeadDeath` [creaturescripts_a_pirates_tail_bosses.lua:tentuglysHeadDeath]
- `CreatureEvent("TentuglysHeadDeath")` registration [creaturescripts_a_pirates_tail_bosses.lua:CreatureEvent]
- `ratmiralBlackwhiskersDeath.onDeath(creature, corpse, killer, mostDamage, unjustified, mostDamage_unjustified)` [creaturescripts_ratmiral_death.lua:ratmiralBlackwhiskersDeath.onDeath]
- `CreatureEvent("RatmiralBlackwhiskersDeath")` assigned to `ratmiralBlackwhiskersDeath` [creaturescripts_ratmiral_death.lua:ratmiralBlackwhiskersDeath]
- `CreatureEvent("RatmiralBlackwhiskersDeath")` registration [creaturescripts_ratmiral_death.lua:CreatureEvent]
- `tentuglysHeadDeath.onDeath(creature, corpse, killer, mostDamage, unjustified, mostDamage_unjustified)` [creaturescripts_tentugly_death.lua:tentuglysHeadDeath.onDeath]
- `CreatureEvent("TentuglysHeadDeath")` assigned to `tentuglysHeadDeath` [creaturescripts_tentugly_death.lua:tentuglysHeadDeath]
- `CreatureEvent("TentuglysHeadDeath")` registration [creaturescripts_tentugly_death.lua:CreatureEvent]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_rascacoon_shortcut.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_a_pirates_tail_bosses.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_cheesy_key.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_cheesy_key.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_rascacoon_shortcut.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_rascacoon_shortcut.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ratmiral_blackwhiskers.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_tentuglys_head.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_a_pirates_tail_bosses.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_a_pirates_tail_bosses.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_ratmiral_death.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_tentugly_death.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_tentugly_death.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
