# The Outlaw Camp

## Overview
Component package under `scripts/quests/the_outlaw_camp` containing 5 files (`actions_oven.lua`..`movements_entrance.lua`).

## Interface
- `theOutlawOven.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_oven.lua:theOutlawOven.onUse]
- `Action()` assigned to `theOutlawOven` [actions_oven.lua:theOutlawOven]
- `Action()` registration [actions_oven.lua:Action]
- `theOutlawPower.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_power_burn.lua:theOutlawPower.onUse]
- `Action()` assigned to `theOutlawPower` [actions_power_burn.lua:theOutlawPower]
- `Action()` registration [actions_power_burn.lua:Action]
- `theOutlawPowerSwitch.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_power_switch.lua:theOutlawPowerSwitch.onUse]
- `Action()` assigned to `theOutlawPowerSwitch` [actions_power_switch.lua:theOutlawPowerSwitch]
- `Action()` registration [actions_power_switch.lua:Action]
- `outlawQuest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_the_outlaw_camp_quest.lua:outlawQuest.onUse]
- `Action()` assigned to `outlawQuest` [actions_the_outlaw_camp_quest.lua:outlawQuest]
- `Action()` registration [actions_the_outlaw_camp_quest.lua:Action]
- `brightSword.onStepIn(creature, item, position, fromPosition)` [movements_entrance.lua:brightSword.onStepIn]
- `MoveEvent()` assigned to `brightSword` [movements_entrance.lua:brightSword]
- `MoveEvent()` registration [movements_entrance.lua:MoveEvent]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_oven.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_power_burn.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_power_switch.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_entrance.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_oven.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_oven.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_power_burn.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_power_burn.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_power_burn.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_power_switch.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_power_switch.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_the_outlaw_camp_quest.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_the_outlaw_camp_quest.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_the_outlaw_camp_quest.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_entrance.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_entrance.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
