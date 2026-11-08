# Secret Service

## Overview
Component package under `scripts/quests/secret_service` containing 8 files (`actions_amazon_disguise_kit.lua`..`movements_pirate.lua`).

## Interface
- `secretServiceKit.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_amazon_disguise_kit.lua:secretServiceKit.onUse]
- `Action()` assigned to `secretServiceKit` [actions_amazon_disguise_kit.lua:secretServiceKit]
- `Action()` registration [actions_amazon_disguise_kit.lua:Action]
- `secretServiceLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lever.lua:secretServiceLever.onUse]
- `Action()` assigned to `secretServiceLever` [actions_lever.lua:secretServiceLever]
- `Action()` registration [actions_lever.lua:Action]
- `secretServiceRing.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_ring.lua:secretServiceRing.onUse]
- `Action()` assigned to `secretServiceRing` [actions_ring.lua:secretServiceRing]
- `Action()` registration [actions_ring.lua:Action]
- `secretServiceBugs.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_rust_bugs.lua:secretServiceBugs.onUse]
- `Action()` assigned to `secretServiceBugs` [actions_rust_bugs.lua:secretServiceBugs]
- `Action()` registration [actions_rust_bugs.lua:Action]
- `secretServiceTools.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_tools.lua:secretServiceTools.onUse]
- `Action()` assigned to `secretServiceTools` [actions_tools.lua:secretServiceTools]
- `Action()` registration [actions_tools.lua:Action]
- `blackKnightKill.onDeath(creature)` [creaturescripts_black_knight_kill.lua:blackKnightKill.onDeath]
- `CreatureEvent("BlackKnightDeath")` assigned to `blackKnightKill` [creaturescripts_black_knight_kill.lua:blackKnightKill]
- `CreatureEvent("BlackKnightDeath")` registration [creaturescripts_black_knight_kill.lua:CreatureEvent]
- `amazon.onStepIn(creature, item, position, fromPosition)` [movements_amazon.lua:amazon.onStepIn]
- `MoveEvent()` assigned to `amazon` [movements_amazon.lua:amazon]
- `MoveEvent()` registration [movements_amazon.lua:MoveEvent]
- `pirate.onStepIn(creature, item, position, fromPosition)` [movements_pirate.lua:pirate.onStepIn]
- `MoveEvent()` assigned to `pirate` [movements_pirate.lua:pirate]
- `MoveEvent()` registration [movements_pirate.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_ring.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_rust_bugs.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_black_knight_kill.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_amazon.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_amazon.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_pirate.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_pirate.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_amazon_disguise_kit.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_amazon_disguise_kit.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_lever.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_lever.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ring.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_ring.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_ring.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_rust_bugs.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_rust_bugs.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_rust_bugs.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_rust_bugs.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
