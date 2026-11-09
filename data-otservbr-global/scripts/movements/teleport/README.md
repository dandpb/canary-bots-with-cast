# Teleport

## Overview
Component package under `scripts/movements/teleport` containing 24 files (`adventurers_guild.lua`..`yalahar_demon.lua`).

## Interface
- `adventurersGuild.onStepIn(creature, item, position, fromPosition)` [adventurers_guild.lua:adventurersGuild.onStepIn]
- `MoveEvent()` assigned to `adventurersGuild` [adventurers_guild.lua:adventurersGuild]
- `MoveEvent()` registration [adventurers_guild.lua:MoveEvent]
- `candia.onStepIn(creature, item, position, fromPosition)` [candia.lua:candia.onStepIn]
- `MoveEvent()` assigned to `candia` [candia.lua:candia]
- `MoveEvent()` registration [candia.lua:MoveEvent]
- `citizen.onStepIn(creature, item, position, fromPosition)` [citizen.lua:citizen.onStepIn]
- `MoveEvent()` assigned to `citizen` [citizen.lua:citizen]
- `MoveEvent()` registration [citizen.lua:MoveEvent]
- `citizenSvargrond.onStepIn(creature, item, position, fromPosition)` [citizen_svargrond.lua:citizenSvargrond.onStepIn]
- `MoveEvent()` assigned to `citizenSvargrond` [citizen_svargrond.lua:citizenSvargrond]
- `MoveEvent()` registration [citizen_svargrond.lua:MoveEvent]
- `revertLever(position)` [dark_cathedral_teleports.lua:revertLever]
- `lever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [dark_cathedral_teleports.lua:lever.onUse]
- `teleport.onStepIn(player, item, position, fromPosition)` [dark_cathedral_teleports.lua:teleport.onStepIn]
- `Action()` assigned to `lever` [dark_cathedral_teleports.lua:lever]
- `Action()` registration [dark_cathedral_teleports.lua:Action]
- `MoveEvent()` assigned to `teleport` [dark_cathedral_teleports.lua:teleport]
- `MoveEvent()` registration [dark_cathedral_teleports.lua:MoveEvent]
- `deeperBanutaShortcutTeleport.onStepIn(creature, item, position, fromPosition)` [deeper_banuta_shortcut_teleport.lua:deeperBanutaShortcutTeleport.onStepIn]
- `MoveEvent()` assigned to `deeperBanutaShortcutTeleport` [deeper_banuta_shortcut_teleport.lua:deeperBanutaShortcutTeleport]
- `MoveEvent()` registration [deeper_banuta_shortcut_teleport.lua:MoveEvent]
- `teleportToDestination(creature, position)` [dragolisk_teleport.lua:teleportToDestination]
- `dragoliskTeleport.onStepIn(creature, item, position, fromPosition)` [dragolisk_teleport.lua:dragoliskTeleport.onStepIn]
- `MoveEvent()` assigned to `dragoliskTeleport` [dragolisk_teleport.lua:dragoliskTeleport]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [adventurers_guild.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [adventurers_guild.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [candia.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [citizen.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [citizen.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [citizen_svargrond.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [citizen_svargrond.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [dark_cathedral_teleports.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [deeper_banuta_shortcut_teleport.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [deeper_banuta_shortcut_teleport.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [dragolisk_teleport.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [fibula.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [adventurers_guild.lua:register]
- Mutates player or global storage state via `setStorageValue` [adventurers_guild.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [adventurers_guild.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [candia.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [candia.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [citizen.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [citizen.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [citizen_svargrond.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [citizen_svargrond.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [dark_cathedral_teleports.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [dark_cathedral_teleports.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [dark_cathedral_teleports.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
