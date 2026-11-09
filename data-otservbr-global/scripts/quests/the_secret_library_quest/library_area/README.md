# Library Area

## Overview
Component package under `scripts/quests/the_secret_library_quest/library_area` containing 13 files (`actions_ghulosh.lua`..`movements_timers.lua`).

## Interface
- `BossLever(config)` assigned to `lever` [actions_ghulosh.lua:lever]
- `BossLever(config)` registration [actions_ghulosh.lua:BossLever]
- `BossLever(config)` assigned to `lever` [actions_gorzindel.lua:lever]
- `BossLever(config)` registration [actions_gorzindel.lua:BossLever]
- `BossLever(config)` assigned to `lever` [actions_lokathmor.lua:lever]
- `BossLever(config)` registration [actions_lokathmor.lua:BossLever]
- `BossLever(config)` assigned to `lever` [actions_mazzinor.lua:lever]
- `BossLever(config)` registration [actions_mazzinor.lua:BossLever]
- `isStuck(mustFree)` [actions_parchment.lua:isStuck]
- `freeRoom()` [actions_parchment.lua:freeRoom]
- `onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_parchment.lua:onUse]
- `Action()` assigned to `actions_library_parchment` [actions_parchment.lua:actions_library_parchment]
- `Action()` registration [actions_parchment.lua:Action]
- `BossLever(config)` assigned to `lever` [actions_the_scourge_of_oblivion.lua:lever]
- `BossLever(config)` registration [actions_the_scourge_of_oblivion.lua:BossLever]
- `nextStage(storage)` [creaturescripts_ghulosh.lua:nextStage]
- `creaturescripts_library_ghulosh.onThink(creature, interval)` [creaturescripts_ghulosh.lua:creaturescripts_library_ghulosh.onThink]
- `doSpawn(monster, k, position)` [creaturescripts_ghulosh.lua:doSpawn]
- `creaturescripts_library_ghulosh.onDeath(creature, corpse, killer, mostDamageKiller, unjustified, mostDamageUnjustified)` [creaturescripts_ghulosh.lua:creaturescripts_library_ghulosh.onDeath]
- `CreatureEvent("ghuloshThink")` assigned to `creaturescripts_library_ghulosh` [creaturescripts_ghulosh.lua:creaturescripts_library_ghulosh]
- `CreatureEvent("ghuloshDeath")` assigned to `creaturescripts_library_ghulosh` [creaturescripts_ghulosh.lua:creaturescripts_library_ghulosh]
- `CreatureEvent("ghuloshThink")` registration [creaturescripts_ghulosh.lua:CreatureEvent]
- `CreatureEvent("ghuloshDeath")` registration [creaturescripts_ghulosh.lua:CreatureEvent]
- `creaturescripts_gorzindel.onDeath(creature, corpse, killer, mostDamageKiller, unjustified, mostDamageUnjustified)` [creaturescripts_gorzindel.lua:creaturescripts_gorzindel.onDeath]
- `creaturescripts_gorzindel.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)` [creaturescripts_gorzindel.lua:creaturescripts_gorzindel.onHealthChange]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_parchment.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_ghulosh.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_gorzindel.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [creaturescripts_mazzinor.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_gorzindel.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_mazzinor.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_timers.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_timers.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ghulosh.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_gorzindel.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lokathmor.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mazzinor.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_parchment.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_parchment.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_parchment.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_the_scourge_of_oblivion.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_ghulosh.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_ghulosh.lua:setStorageValue]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [creaturescripts_ghulosh.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [creaturescripts_ghulosh.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
