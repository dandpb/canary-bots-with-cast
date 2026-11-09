# The Secret Library Quest

## Overview
Provides 3 direct files (`creaturescripts_kill.lua`..`movement_teleport.lua`) and 7 subdirectories under `scripts/quests/the_secret_library_quest`.

## Interface
- `creaturescripts_library_bosses.onDeath(creature, corpse, killer, mostDamageKiller, lastHitUnjustified)` [creaturescripts_kill.lua:creaturescripts_library_bosses.onDeath]
- `CreatureEvent("killingLibrary")` assigned to `creaturescripts_library_bosses` [creaturescripts_kill.lua:creaturescripts_library_bosses]
- `CreatureEvent("killingLibrary")` registration [creaturescripts_kill.lua:CreatureEvent]
- `creaturescripts_library_login.onLogin(player)` [creaturescripts_login.lua:creaturescripts_library_login.onLogin]
- `CreatureEvent("loginLibrary")` assigned to `creaturescripts_library_login` [creaturescripts_login.lua:creaturescripts_library_login]
- `CreatureEvent("loginLibrary")` registration [creaturescripts_login.lua:CreatureEvent]
- `library.onStepIn(creature, item, position, fromPosition)` [movement_teleport.lua:library.onStepIn]
- `MoveEvent()` assigned to `library` [movement_teleport.lua:library]
- `MoveEvent()` registration [movement_teleport.lua:MoveEvent]
- [bursting_at_the_seams_museum](./bursting_at_the_seams_museum/README.md) - Component package under `scripts/quests/the_secret_library_quest/bursting_at_the_seams_museum` containing 6 files (`actions_bony_rod.lua`..`movements_teleportTo.lua`).
- [high_and_dry_isles](./high_and_dry_isles/README.md) - Component package under `scripts/quests/the_secret_library_quest/high_and_dry_isles` containing 3 files (`actions_telescope.lua`..`movements_stepIn.lua`).
- [library_area](./library_area/README.md) - Component package under `scripts/quests/the_secret_library_quest/library_area` containing 13 files (`actions_ghulosh.lua`..`movements_timers.lua`).
- [liquid_death](./liquid_death/README.md) - Component package under `scripts/quests/the_secret_library_quest/liquid_death` containing 4 files (`actions_brokulLever.lua`..`movements_teleportTo.lua`).
- [the_lament_asuras](./the_lament_asuras/README.md) - Component package under `scripts/quests/the_secret_library_quest/the_lament_asuras` containing 7 files (`actions_bonefiddle.lua`..`movements_elemental_portals.lua`).
- [the_order_of_the_falcon](./the_order_of_the_falcon/README.md) - Component package under `scripts/quests/the_secret_library_quest/the_order_of_the_falcon` containing 4 files (`actions_doors.lua`..`movements_bossEntrance.lua`).
- [the_parth_of_defiances_desert](./the_parth_of_defiances_desert/README.md) - Component package under `scripts/quests/the_secret_library_quest/the_parth_of_defiances_desert` containing 6 files (`actions_chests.lua`..`movements_teleportTo.lua`).

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_kill.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movement_teleport.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_kill.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_kill.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_login.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movement_teleport.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [movement_teleport.lua:teleportTo]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
