# Bosses

## Overview
Component package under `monster/quests/bigfoots_burden/bosses` containing 3 files (`abyssador.lua`..`gnomevil.lua`).

## Interface
- `Game.createMonsterType("Abyssador")` and `mType:register(monster)` [abyssador.lua:Game.createMonsterType]
- `Game.createMonsterType("Deathstrike")` and `mType:register(monster)` [deathstrike.lua:Game.createMonsterType]
- `Game.createMonsterType("Gnomevil")` and `mType:register(monster)` [gnomevil.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [abyssador.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [deathstrike.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [gnomevil.lua:monster.flags]

## Side Effects
- Registers monster type `Abyssador` into the global `Game` engine registry via `mType:register(monster)` [abyssador.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [abyssador.lua:monster.events]
- Registers monster type `Deathstrike` into the global `Game` engine registry via `mType:register(monster)` [deathstrike.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [deathstrike.lua:monster.events]
- Registers monster type `Gnomevil` into the global `Game` engine registry via `mType:register(monster)` [gnomevil.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [gnomevil.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
