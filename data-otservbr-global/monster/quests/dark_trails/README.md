# Dark Trails

## Overview
Component package under `monster/quests/dark_trails` containing 9 files (`canopic_jar.lua`..`tremor_worm.lua`).

## Interface
- `Game.createMonsterType("Canopic Jar")` and `mType:register(monster)` [canopic_jar.lua:Game.createMonsterType]
- `Game.createMonsterType("Death Priest Shargon")` and `mType:register(monster)` [death_priest_shargon.lua:Game.createMonsterType]
- `Game.createMonsterType("Depowered Minotaur")` and `mType:register(monster)` [depowered_minotaur.lua:Game.createMonsterType]
- `Game.createMonsterType("Greater Canopic Jar")` and `mType:register(monster)` [greater_canopic_jar.lua:Game.createMonsterType]
- `Game.createMonsterType("Greater Death Minion")` and `mType:register(monster)` [greater_death_minion.lua:Game.createMonsterType]
- `Game.createMonsterType("Lesser Death Minion")` and `mType:register(monster)` [lesser_death_minion.lua:Game.createMonsterType]
- `Game.createMonsterType("Superior Death Minion")` and `mType:register(monster)` [superior_death_minion.lua:Game.createMonsterType]
- `Game.createMonsterType("The Ravager")` and `mType:register(monster)` [the_ravager.lua:Game.createMonsterType]
- `Game.createMonsterType("Tremor Worm")` and `mType:register(monster)` [tremor_worm.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [canopic_jar.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [death_priest_shargon.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [depowered_minotaur.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [greater_canopic_jar.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [greater_death_minion.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lesser_death_minion.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [superior_death_minion.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_ravager.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [tremor_worm.lua:monster.flags]

## Side Effects
- Registers monster type `Canopic Jar` into the global `Game` engine registry via `mType:register(monster)` [canopic_jar.lua:mType:register]
- Registers monster type `Death Priest Shargon` into the global `Game` engine registry via `mType:register(monster)` [death_priest_shargon.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [death_priest_shargon.lua:monster.events]
- Registers monster type `Depowered Minotaur` into the global `Game` engine registry via `mType:register(monster)` [depowered_minotaur.lua:mType:register]
- Registers monster type `Greater Canopic Jar` into the global `Game` engine registry via `mType:register(monster)` [greater_canopic_jar.lua:mType:register]
- Registers monster type `Greater Death Minion` into the global `Game` engine registry via `mType:register(monster)` [greater_death_minion.lua:mType:register]
- Registers monster type `Lesser Death Minion` into the global `Game` engine registry via `mType:register(monster)` [lesser_death_minion.lua:mType:register]
- Registers monster type `Superior Death Minion` into the global `Game` engine registry via `mType:register(monster)` [superior_death_minion.lua:mType:register]
- Registers monster type `The Ravager` into the global `Game` engine registry via `mType:register(monster)` [the_ravager.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [the_ravager.lua:monster.events]
- Registers monster type `Tremor Worm` into the global `Game` engine registry via `mType:register(monster)` [tremor_worm.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
