# Roshamuul Quest

## Overview
Component package under `scripts/quests/roshamuul_quest` containing 9 files (`actions_bone.lua`..`movements_lower_roshamuul.lua`).

## Interface
- `revertBone(position, itemId, transformId)` [actions_bone.lua:revertBone]
- `lowerRoshamuulBone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bone.lua:lowerRoshamuulBone.onUse]
- `Action()` assigned to `lowerRoshamuulBone` [actions_bone.lua:lowerRoshamuulBone]
- `Action()` registration [actions_bone.lua:Action]
- `lowerRoshamuulChalk.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_chalk.lua:lowerRoshamuulChalk.onUse]
- `Action()` assigned to `lowerRoshamuulChalk` [actions_chalk.lua:lowerRoshamuulChalk]
- `Action()` registration [actions_chalk.lua:Action]
- `lowerRoshamuulGravel.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_gravel.lua:lowerRoshamuulGravel.onUse]
- `Action()` assigned to `lowerRoshamuulGravel` [actions_gravel.lua:lowerRoshamuulGravel]
- `Action()` registration [actions_gravel.lua:Action]
- `lowerRoshamuulMixtune.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mixture.lua:lowerRoshamuulMixtune.onUse]
- `Action()` assigned to `lowerRoshamuulMixtune` [actions_mixture.lua:lowerRoshamuulMixtune]
- `Action()` registration [actions_mixture.lua:Action]
- `lowerRoshamuulMortar.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mortar.lua:lowerRoshamuulMortar.onUse]
- `Action()` assigned to `lowerRoshamuulMortar` [actions_mortar.lua:lowerRoshamuulMortar]
- `Action()` registration [actions_mortar.lua:Action]
- `raids(monster)` [actions_resonance_chamber.lua:raids]
- `cleanRaid()` [actions_resonance_chamber.lua:cleanRaid]
- `lowerRoshamuulChamber.onUse(cid, item, fromPosition, itemEx, toPosition)` [actions_resonance_chamber.lua:lowerRoshamuulChamber.onUse]
- `Action()` assigned to `lowerRoshamuulChamber` [actions_resonance_chamber.lua:lowerRoshamuulChamber]
- `Action()` registration [actions_resonance_chamber.lua:Action]
- `lowerRoshamuulTrough.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_trough.lua:lowerRoshamuulTrough.onUse]
- `Action()` assigned to `lowerRoshamuulTrough` [actions_trough.lua:lowerRoshamuulTrough]
- `Action()` registration [actions_trough.lua:Action]
- `lowerRoshamuul.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_lower_roshamuul.lua:lowerRoshamuul.onDeath]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_bone.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_resonance_chamber.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_resonance_chamber.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_resonance_chamber.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_trough.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_lower_roshamuul.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_lower_roshamuul.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bone.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bone.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_bone.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_chalk.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_chalk.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_gravel.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_gravel.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mixture.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mixture.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mortar.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_mortar.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_resonance_chamber.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
