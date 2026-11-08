# No Rest For The Wicked

## Overview
Intermediate blueprint grouping 2 subdirectories under `monster/quests/no_rest_for_the_wicked`.

## Subdirectories & Boundaries
- [bosses](./bosses/README.md) - Component package under `monster/quests/no_rest_for_the_wicked/bosses` containing 1 files (`arbaziloth.lua`..`arbaziloth.lua`).
- [summons](./summons/README.md) - Component package under `monster/quests/no_rest_for_the_wicked/summons` containing 1 files (`overcharged_demon.lua`..`overcharged_demon.lua`).

## Interface
- `Game.createMonsterType("Arbaziloth")` and `mType:register(monster)` [arbaziloth.lua:Game.createMonsterType]
- `mType.onAppear` lifecycle callback [arbaziloth.lua:mType.onAppear]
- `Game.createMonsterType("Overcharged Demon")` and `mType:register(monster)` [overcharged_demon.lua:Game.createMonsterType]
- [bosses](./bosses/README.md) - Component package under `monster/quests/no_rest_for_the_wicked/bosses` containing 1 files (`arbaziloth.lua`..`arbaziloth.lua`).
- [summons](./summons/README.md) - Component package under `monster/quests/no_rest_for_the_wicked/summons` containing 1 files (`overcharged_demon.lua`..`overcharged_demon.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [arbaziloth.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [overcharged_demon.lua:monster.flags]

## Side Effects
- Registers monster type `Arbaziloth` into the global `Game` engine registry via `mType:register(monster)` [arbaziloth.lua:mType:register]
- Registers monster type `Overcharged Demon` into the global `Game` engine registry via `mType:register(monster)` [overcharged_demon.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
