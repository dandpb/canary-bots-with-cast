# The Ice Islands Quest

## Overview
Component package under `scripts/quests/the_ice_islands_quest` containing 8 files (`actions_anthill.lua`..`movements_nibelor_dog_led.lua`).

## Interface
- `iceAntHill.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_anthill.lua:iceAntHill.onUse]
- `Action()` assigned to `iceAntHill` [actions_anthill.lua:iceAntHill]
- `Action()` registration [actions_anthill.lua:Action]
- `iceCharm.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_charm.lua:iceCharm.onUse]
- `Action()` assigned to `iceCharm` [actions_charm.lua:iceCharm]
- `Action()` registration [actions_charm.lua:Action]
- `iceCure.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_cure.lua:iceCure.onUse]
- `Action()` assigned to `iceCure` [actions_cure.lua:iceCure]
- `Action()` registration [actions_cure.lua:Action]
- `transformBack(position, itemId, transformId)` [actions_paint.lua:transformBack]
- `icePaint.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_paint.lua:icePaint.onUse]
- `Action()` assigned to `icePaint` [actions_paint.lua:icePaint]
- `Action()` registration [actions_paint.lua:Action]
- `summonMonster(name, position)` [actions_yakchal.lua:summonMonster]
- `iceYakchal.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_yakchal.lua:iceYakchal.onUse]
- `Action()` assigned to `iceYakchal` [actions_yakchal.lua:iceYakchal]
- `Action()` registration [actions_yakchal.lua:Action]
- `huskyKill.onDeath(creature)` [creaturescripts_husky_kill.lua:huskyKill.onDeath]
- `CreatureEvent("HuskyDeath")` assigned to `huskyKill` [creaturescripts_husky_kill.lua:huskyKill]
- `CreatureEvent("HuskyDeath")` registration [creaturescripts_husky_kill.lua:CreatureEvent]
- `helheim.onStepIn(creature, item, position, fromPosition)` [movements_helheim.lua:helheim.onStepIn]
- `MoveEvent()` assigned to `helheim` [movements_helheim.lua:helheim]
- `MoveEvent()` registration [movements_helheim.lua:MoveEvent]
- `nibelorDogLed.onStepIn(creature, item, position, fromPosition)` [movements_nibelor_dog_led.lua:nibelorDogLed.onStepIn]
- `MoveEvent()` assigned to `nibelorDogLed` [movements_nibelor_dog_led.lua:nibelorDogLed]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_anthill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_charm.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_cure.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_paint.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_paint.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_yakchal.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_husky_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_helheim.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_helheim.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_nibelor_dog_led.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_nibelor_dog_led.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_anthill.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_anthill.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_anthill.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_charm.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_charm.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_cure.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_cure.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_paint.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_paint.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_paint.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_paint.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_yakchal.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
