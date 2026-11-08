# Hero Of Rathleton

## Overview
Component package under `scripts/quests/hero_of_rathleton` containing 15 files (`actions_machines_deep_terror.lua`..`movements_professor_maxxen.lua`).

## Interface
- `revertMachine(position, itemId, transformId)` [actions_machines_deep_terror.lua:revertMachine]
- `heroRathletonDeep.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_machines_deep_terror.lua:heroRathletonDeep.onUse]
- `Action()` assigned to `heroRathletonDeep` [actions_machines_deep_terror.lua:heroRathletonDeep]
- `Action()` registration [actions_machines_deep_terror.lua:Action]
- `revertMachine(position, itemId, transformId)` [actions_machines_glooth_horror.lua:revertMachine]
- `heroRathletonGlooth.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_machines_glooth_horror.lua:heroRathletonGlooth.onUse]
- `Action()` assigned to `heroRathletonGlooth` [actions_machines_glooth_horror.lua:heroRathletonGlooth]
- `Action()` registration [actions_machines_glooth_horror.lua:Action]
- `revertMachine(position, itemId, transformId)` [actions_machines_lava.lua:revertMachine]
- `heroRathletonLava.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_machines_lava.lua:heroRathletonLava.onUse]
- `Action()` assigned to `heroRathletonLava` [actions_machines_lava.lua:heroRathletonLava]
- `Action()` registration [actions_machines_lava.lua:Action]
- `revertMachine(position, itemId, transformId)` [actions_machines_professor_maxxen.lua:revertMachine]
- `heroRathletonProfessor.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_machines_professor_maxxen.lua:heroRathletonProfessor.onUse]
- `Action()` assigned to `heroRathletonProfessor` [actions_machines_professor_maxxen.lua:heroRathletonProfessor]
- `Action()` registration [actions_machines_professor_maxxen.lua:Action]
- `heroRathletonCorpse.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_raging_corpse.lua:heroRathletonCorpse.onUse]
- `Action()` assigned to `heroRathletonCorpse` [actions_raging_corpse.lua:heroRathletonCorpse]
- `Action()` registration [actions_raging_corpse.lua:Action]
- `heroRathletonReward.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_reward.lua:heroRathletonReward.onUse]
- `Action()` assigned to `heroRathletonReward` [actions_reward.lua:heroRathletonReward]
- `Action()` registration [actions_reward.lua:Action]
- `checkHorror()` [creaturescripts_bosses_kill.lua:checkHorror]
- `revertTeleport(position, itemId, transformId, destination)` [creaturescripts_bosses_kill.lua:revertTeleport]
- `rathletonBossKill.onDeath(creature)` [creaturescripts_bosses_kill.lua:rathletonBossKill.onDeath]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_machines_deep_terror.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_machines_deep_terror.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_machines_glooth_horror.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_machines_glooth_horror.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_machines_lava.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_machines_lava.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_machines_professor_maxxen.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_machines_professor_maxxen.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_raging_corpse.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_reward.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_bosses_kill.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_tentacle.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_machines_deep_terror.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_machines_deep_terror.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_machines_deep_terror.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_machines_deep_terror.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_machines_glooth_horror.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_machines_glooth_horror.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_machines_glooth_horror.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_machines_glooth_horror.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_machines_lava.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_machines_lava.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_machines_lava.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_machines_lava.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
