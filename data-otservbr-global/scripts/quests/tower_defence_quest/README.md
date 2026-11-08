# Tower Defence Quest

## Overview
Component package under `scripts/quests/tower_defence_quest` containing 1 files (`creaturescripts_goblin_leader_kill.lua`..`creaturescripts_goblin_leader_kill.lua`).

## Interface
- `creaturescripts_goblin_leader_kill.onDeath(creature)` [creaturescripts_goblin_leader_kill.lua:creaturescripts_goblin_leader_kill.onDeath]
- `CreatureEvent("GoblinLeaderDeath")` assigned to `creaturescripts_goblin_leader_kill` [creaturescripts_goblin_leader_kill.lua:creaturescripts_goblin_leader_kill]
- `CreatureEvent("GoblinLeaderDeath")` registration [creaturescripts_goblin_leader_kill.lua:CreatureEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_goblin_leader_kill.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_goblin_leader_kill.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_goblin_leader_kill.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
