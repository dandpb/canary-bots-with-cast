# Summons

## Overview
Component package under `monster/quests/ferumbras_ascension/summons` containing 3 files (`enthralled_demon.lua`..`rift_invader.lua`).

## Interface
- `Game.createMonsterType("Enthralled Demon")` and `mType:register(monster)` [enthralled_demon.lua:Game.createMonsterType]
- `Game.createMonsterType("Rift Fragment")` and `mType:register(monster)` [rift_fragment.lua:Game.createMonsterType]
- `Game.createMonsterType("Rift Invader")` and `mType:register(monster)` [rift_invader.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [enthralled_demon.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rift_fragment.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rift_invader.lua:monster.flags]

## Side Effects
- Registers monster type `Enthralled Demon` into the global `Game` engine registry via `mType:register(monster)` [enthralled_demon.lua:mType:register]
- Registers monster type `Rift Fragment` into the global `Game` engine registry via `mType:register(monster)` [rift_fragment.lua:mType:register]
- Registers monster type `Rift Invader` into the global `Game` engine registry via `mType:register(monster)` [rift_invader.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [rift_invader.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
