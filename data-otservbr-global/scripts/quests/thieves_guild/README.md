# Thieves Guild

## Overview
Component package under `scripts/quests/thieves_guild` containing 1 files (`creaturescripts_nomad_kill.lua`..`creaturescripts_nomad_kill.lua`).

## Interface
- `nomadKill.onDeath(creature, _corpse, _lastHitKiller, mostDamageKiller)` [creaturescripts_nomad_kill.lua:nomadKill.onDeath]
- `CreatureEvent("NomadDeath")` assigned to `nomadKill` [creaturescripts_nomad_kill.lua:nomadKill]
- `CreatureEvent("NomadDeath")` registration [creaturescripts_nomad_kill.lua:CreatureEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_nomad_kill.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_nomad_kill.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_nomad_kill.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
