# Svargrond Arena

## Overview
Intermediate blueprint grouping 3 subdirectories under `monster/quests/svargrond_arena`.

## Subdirectories & Boundaries
- [greenhorn](./greenhorn/README.md) - Component package under `monster/quests/svargrond_arena/greenhorn` containing 10 files (`achad.lua`..`the_hairy_one.lua`).
- [scrapper](./scrapper/README.md) - Component package under `monster/quests/svargrond_arena/scrapper` containing 10 files (`avalanche.lua`..`the_hag.lua`).
- [warlord](./warlord/README.md) - Component package under `monster/quests/svargrond_arena/warlord` containing 10 files (`darakan_the_executioner.lua`..`webster.lua`).

## Interface
- `Game.createMonsterType("Achad")` and `mType:register(monster)` [achad.lua:Game.createMonsterType]
- `Game.createMonsterType("Axeitus Headbanger")` and `mType:register(monster)` [axeitus_headbanger.lua:Game.createMonsterType]
- `Game.createMonsterType("Avalanche")` and `mType:register(monster)` [avalanche.lua:Game.createMonsterType]
- `Game.createMonsterType("Drasilla")` and `mType:register(monster)` [drasilla.lua:Game.createMonsterType]
- `Game.createMonsterType("Darakan the Executioner")` and `mType:register(monster)` [darakan_the_executioner.lua:Game.createMonsterType]
- `Game.createMonsterType("Deathbringer")` and `mType:register(monster)` [deathbringer.lua:Game.createMonsterType]
- [greenhorn](./greenhorn/README.md) - Component package under `monster/quests/svargrond_arena/greenhorn` containing 10 files (`achad.lua`..`the_hairy_one.lua`).
- [scrapper](./scrapper/README.md) - Component package under `monster/quests/svargrond_arena/scrapper` containing 10 files (`avalanche.lua`..`the_hag.lua`).
- [warlord](./warlord/README.md) - Component package under `monster/quests/svargrond_arena/warlord` containing 10 files (`darakan_the_executioner.lua`..`webster.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [achad.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [avalanche.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [darakan_the_executioner.lua:monster.flags]

## Side Effects
- Registers monster type `Achad` into the global `Game` engine registry via `mType:register(monster)` [achad.lua:mType:register]
- Registers monster type `Avalanche` into the global `Game` engine registry via `mType:register(monster)` [avalanche.lua:mType:register]
- Registers monster type `Darakan the Executioner` into the global `Game` engine registry via `mType:register(monster)` [darakan_the_executioner.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
