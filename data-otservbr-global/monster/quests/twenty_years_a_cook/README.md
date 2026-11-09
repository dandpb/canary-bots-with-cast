# Twenty Years A Cook

## Overview
Intermediate blueprint grouping 1 subdirectories under `monster/quests/twenty_years_a_cook`.

## Subdirectories & Boundaries
- [bosses](./bosses/README.md) - Component package under `monster/quests/twenty_years_a_cook/bosses` containing 1 files (`dragon_hoard.lua`..`dragon_hoard.lua`).

## Interface
- `Game.createMonsterType("Dragon Hoard")` and `mType:register(monster)` [dragon_hoard.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [dragon_hoard.lua:mType.onThink]
- [bosses](./bosses/README.md) - Component package under `monster/quests/twenty_years_a_cook/bosses` containing 1 files (`dragon_hoard.lua`..`dragon_hoard.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragon_hoard.lua:monster.flags]

## Side Effects
- Registers monster type `Dragon Hoard` into the global `Game` engine registry via `mType:register(monster)` [dragon_hoard.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
