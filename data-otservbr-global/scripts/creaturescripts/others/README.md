# Others

## Overview
Component package under `scripts/creaturescripts/others` containing 5 files (`dawnport.lua`..`rookgaard_advance.lua`).

## Interface
- `teleportToDawnportTemple(uid)` [dawnport.lua:teleportToDawnportTemple]
- `dawnportAdvance.onAdvance(player, skill, oldLevel, newLevel)` [dawnport.lua:dawnportAdvance.onAdvance]
- `CreatureEvent("DawnportAdvance")` assigned to `dawnportAdvance` [dawnport.lua:dawnportAdvance]
- `CreatureEvent("DawnportAdvance")` registration [dawnport.lua:CreatureEvent]
- `dropLoot.onDeath(player, corpse, killer, mostDamage, unjustified, mostDamage_unjustified)` [droploot.lua:dropLoot.onDeath]
- `CreatureEvent("DropLoot")` assigned to `dropLoot` [droploot.lua:dropLoot]
- `CreatureEvent("DropLoot")` registration [droploot.lua:CreatureEvent]
- `dofile(CORE_DIRECTORY .. "/libs/systems/blessing.lua")` module loader [droploot.lua:dofile]
- `playerLogin.onLogin(player)` [login.lua:playerLogin.onLogin]
- `CreatureEvent("PlayerLogin")` assigned to `playerLogin` [login.lua:playerLogin]
- `CreatureEvent("PlayerLogin")` registration [login.lua:CreatureEvent]
- `loginEvents.onLogin(player)` [login_events.lua:loginEvents.onLogin]
- `CreatureEvent("LoginEvents")` assigned to `loginEvents` [login_events.lua:loginEvents]
- `CreatureEvent("LoginEvents")` registration [login_events.lua:CreatureEvent]
- `rookgaardAdvance.onAdvance(player, skill, oldLevel, newLevel)` [rookgaard_advance.lua:rookgaardAdvance.onAdvance]
- `CreatureEvent("RookgaardAdvance")` assigned to `rookgaardAdvance` [rookgaard_advance.lua:rookgaardAdvance]
- `CreatureEvent("RookgaardAdvance")` registration [rookgaard_advance.lua:CreatureEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [dawnport.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [dawnport.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [dawnport.lua:teleportTo]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [dawnport.lua:addEvent]
- Loads and executes `CORE_DIRECTORY .. "/libs/systems/blessing.lua"` via `dofile` [droploot.lua:dofile]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [droploot.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [login.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [login.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [login_events.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [rookgaard_advance.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
