# The Lament Asuras

## Overview
Component package under `scripts/quests/the_secret_library_quest/the_lament_asuras` containing 7 files (`actions_bonefiddle.lua`..`movements_elemental_portals.lua`).

## Interface
- `actions_asura_bonefiddle.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_bonefiddle.lua:actions_asura_bonefiddle.onUse]
- `Action()` assigned to `actions_asura_bonefiddle` [actions_bonefiddle.lua:actions_asura_bonefiddle]
- `Action()` registration [actions_bonefiddle.lua:Action]
- `actions_asura_doors.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_doors.lua:actions_asura_doors.onUse]
- `Action()` assigned to `actions_asura_doors` [actions_doors.lua:actions_asura_doors]
- `Action()` registration [actions_doors.lua:Action]
- `actions_asura_fragrance.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_fragrance.lua:actions_asura_fragrance.onUse]
- `Action()` assigned to `actions_asura_fragrance` [actions_fragrance.lua:actions_asura_fragrance]
- `Action()` registration [actions_fragrance.lua:Action]
- `revert(position)` [actions_keys.lua:revert]
- `actions_asura_keys.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_keys.lua:actions_asura_keys.onUse]
- `Action()` assigned to `actions_asura_keys` [actions_keys.lua:actions_asura_keys]
- `Action()` registration [actions_keys.lua:Action]
- `actions_asura_mirror.onUse(player, item, fromPosition, itemEx, toPosition)` [actions_mirror.lua:actions_asura_mirror.onUse]
- `Action()` assigned to `actions_asura_mirror` [actions_mirror.lua:actions_asura_mirror]
- `Action()` registration [actions_mirror.lua:Action]
- `creaturescripts_asuras_mechanic.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)` [creaturescripts_asuras_mechanic.lua:creaturescripts_asuras_mechanic.onHealthChange]
- `CreatureEvent("AsurasMechanic")` assigned to `creaturescripts_asuras_mechanic` [creaturescripts_asuras_mechanic.lua:creaturescripts_asuras_mechanic]
- `CreatureEvent("AsurasMechanic")` registration [creaturescripts_asuras_mechanic.lua:CreatureEvent]
- `isPlayerInRoom(fromPos, toPos)` [movements_elemental_portals.lua:isPlayerInRoom]
- `clearBossRoom(fromPos, toPos, exitPos)` [movements_elemental_portals.lua:clearBossRoom]
- `startBattle(pid, position, b_name, middle)` [movements_elemental_portals.lua:startBattle]
- `expelPlayerFromRoom(cid, fromPos, toPos, exitPos)` [movements_elemental_portals.lua:expelPlayerFromRoom]
- `movements_asura_elemental_portals.onStepIn(creature, item, position, fromPosition)` [movements_elemental_portals.lua:movements_asura_elemental_portals.onStepIn]
- `MoveEvent()` assigned to `movements_asura_elemental_portals` [movements_elemental_portals.lua:movements_asura_elemental_portals]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_bonefiddle.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_doors.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_doors.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_keys.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_mirror.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_asuras_mechanic.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [creaturescripts_asuras_mechanic.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_elemental_portals.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_elemental_portals.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movements_elemental_portals.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_bonefiddle.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_bonefiddle.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_bonefiddle.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_doors.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_doors.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_doors.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_fragrance.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_fragrance.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_fragrance.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_keys.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_keys.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_keys.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
