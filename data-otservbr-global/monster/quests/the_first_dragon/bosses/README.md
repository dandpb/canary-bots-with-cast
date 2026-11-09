# Bosses

## Overview
Component package under `monster/quests/the_first_dragon/bosses` containing 5 files (`fallen_challenger.lua`..`zorvorax.lua`).

## Interface
- `Game.createMonsterType("Fallen Challenger")` and `mType:register(monster)` [fallen_challenger.lua:Game.createMonsterType]
- `Game.createMonsterType("Gelidrazah the Frozen")` and `mType:register(monster)` [gelidrazah_the_frozen.lua:Game.createMonsterType]
- `Game.createMonsterType("Kalyassa")` and `mType:register(monster)` [kalyassa.lua:Game.createMonsterType]
- `Game.createMonsterType("Tazhadur")` and `mType:register(monster)` [tazhadur.lua:Game.createMonsterType]
- `Game.createMonsterType("Zorvorax")` and `mType:register(monster)` [zorvorax.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fallen_challenger.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [gelidrazah_the_frozen.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [kalyassa.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [tazhadur.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [zorvorax.lua:monster.flags]

## Side Effects
- Registers monster type `Fallen Challenger` into the global `Game` engine registry via `mType:register(monster)` [fallen_challenger.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [fallen_challenger.lua:monster.events]
- Registers monster type `Gelidrazah the Frozen` into the global `Game` engine registry via `mType:register(monster)` [gelidrazah_the_frozen.lua:mType:register]
- Registers monster type `Kalyassa` into the global `Game` engine registry via `mType:register(monster)` [kalyassa.lua:mType:register]
- Registers monster type `Tazhadur` into the global `Game` engine registry via `mType:register(monster)` [tazhadur.lua:mType:register]
- Registers monster type `Zorvorax` into the global `Game` engine registry via `mType:register(monster)` [zorvorax.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
