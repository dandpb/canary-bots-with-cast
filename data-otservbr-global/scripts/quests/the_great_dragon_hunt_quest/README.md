# The Great Dragon Hunt Quest

## Overview
Component package under `scripts/quests/the_great_dragon_hunt_quest` containing 3 files (`actions_treasure.lua`..`creaturescripts_the_great_dragon_hunt.lua`).

## Interface
- `adventurersTreasure.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_treasure.lua:adventurersTreasure.onUse]
- `Action()` assigned to `adventurersTreasure` [actions_treasure.lua:adventurersTreasure]
- `Action()` registration [actions_treasure.lua:Action]
- `adventurersWarriorSkeleton.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_warrior_skeleton.lua:adventurersWarriorSkeleton.onUse]
- `Action()` assigned to `adventurersWarriorSkeleton` [actions_warrior_skeleton.lua:adventurersWarriorSkeleton]
- `Action()` registration [actions_warrior_skeleton.lua:Action]
- `adventurersGuildHunt.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_the_great_dragon_hunt.lua:adventurersGuildHunt.onDeath]
- `CreatureEvent("TheGreatDragonHuntDeath")` assigned to `adventurersGuildHunt` [creaturescripts_the_great_dragon_hunt.lua:adventurersGuildHunt]
- `CreatureEvent("TheGreatDragonHuntDeath")` registration [creaturescripts_the_great_dragon_hunt.lua:CreatureEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_treasure.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_warrior_skeleton.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_the_great_dragon_hunt.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_treasure.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_treasure.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_treasure.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_warrior_skeleton.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_warrior_skeleton.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_warrior_skeleton.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_the_great_dragon_hunt.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_the_great_dragon_hunt.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
