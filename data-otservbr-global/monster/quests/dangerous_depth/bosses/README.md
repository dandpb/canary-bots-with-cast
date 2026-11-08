# Bosses

## Overview
Component package under `monster/quests/dangerous_depth/bosses` containing 6 files (`ancient_spawn_of_morgathla.lua`..`the_hungry_baron_from_below.lua`).

## Interface
- `Game.createMonsterType("Ancient Spawn of Morgathla")` and `mType:register(monster)` [ancient_spawn_of_morgathla.lua:Game.createMonsterType]
- `Game.createMonsterType("The Baron from Below")` and `mType:register(monster)` [the_baron_from_below.lua:Game.createMonsterType]
- `Game.createMonsterType("The Count of the Core")` and `mType:register(monster)` [the_count_of_the_core.lua:Game.createMonsterType]
- `Game.createMonsterType("The Duke of the Depths")` and `mType:register(monster)` [the_duke_of_the_depths.lua:Game.createMonsterType]
- `Game.createMonsterType("The Fire Empowered Duke")` and `mType:register(monster)` [the_duke_of_the_depths_immortal.lua:Game.createMonsterType]
- `Game.createMonsterType("The Hungry Baron from Below")` and `mType:register(monster)` [the_hungry_baron_from_below.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ancient_spawn_of_morgathla.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_baron_from_below.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_count_of_the_core.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_duke_of_the_depths.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_duke_of_the_depths_immortal.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_hungry_baron_from_below.lua:monster.flags]

## Side Effects
- Registers monster type `Ancient Spawn of Morgathla` into the global `Game` engine registry via `mType:register(monster)` [ancient_spawn_of_morgathla.lua:mType:register]
- Registers monster type `The Baron from Below` into the global `Game` engine registry via `mType:register(monster)` [the_baron_from_below.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [the_baron_from_below.lua:monster.events]
- Registers monster type `The Count of the Core` into the global `Game` engine registry via `mType:register(monster)` [the_count_of_the_core.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [the_count_of_the_core.lua:monster.events]
- Registers monster type `The Duke of the Depths` into the global `Game` engine registry via `mType:register(monster)` [the_duke_of_the_depths.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [the_duke_of_the_depths.lua:monster.events]
- Registers monster type `The Fire Empowered Duke` into the global `Game` engine registry via `mType:register(monster)` [the_duke_of_the_depths_immortal.lua:mType:register]
- Registers monster type `The Hungry Baron from Below` into the global `Game` engine registry via `mType:register(monster)` [the_hungry_baron_from_below.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
