# Primal Ordeal Quest

## Overview
Component package under `monster/quests/primal_ordeal_quest` containing 7 files (`lava_creature.lua`..`unchained_fire.lua`).

## Interface
- `Game.createMonsterType("Lava Creature")` and `mType:register(monster)` [lava_creature.lua:Game.createMonsterType]
- `Game.createMonsterType("Magma Bubble")` and `mType:register(monster)` [magma_bubble.lua:Game.createMonsterType]
- `Game.createMonsterType("Magma Crystal")` and `mType:register(monster)` [magma_crystal.lua:Game.createMonsterType]
- `Game.createMonsterType("Plunder Patriarch")` and `mType:register(monster)` [plunder_patriarch.lua:Game.createMonsterType]
- `Game.createMonsterType("The End of Days")` and `mType:register(monster)` [the_end_of_days.lua:Game.createMonsterType]
- `Game.createMonsterType("The Primal Menace")` and `mType:register(monster)` [the_primal_menace.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [the_primal_menace.lua:mType.onThink]
- `Game.createMonsterType("Unchained Fire")` and `mType:register(monster)` [unchained_fire.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lava_creature.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [magma_bubble.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [magma_crystal.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [plunder_patriarch.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_end_of_days.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_primal_menace.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [unchained_fire.lua:monster.flags]

## Side Effects
- Registers monster type `Lava Creature` into the global `Game` engine registry via `mType:register(monster)` [lava_creature.lua:mType:register]
- Registers monster type `Magma Bubble` into the global `Game` engine registry via `mType:register(monster)` [magma_bubble.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [magma_bubble.lua:monster.events]
- Registers monster type `Magma Crystal` into the global `Game` engine registry via `mType:register(monster)` [magma_crystal.lua:mType:register]
- Registers monster type `Plunder Patriarch` into the global `Game` engine registry via `mType:register(monster)` [plunder_patriarch.lua:mType:register]
- Registers monster type `The End of Days` into the global `Game` engine registry via `mType:register(monster)` [the_end_of_days.lua:mType:register]
- Registers monster type `The Primal Menace` into the global `Game` engine registry via `mType:register(monster)` [the_primal_menace.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [the_primal_menace.lua:monster.events]
- Registers monster type `Unchained Fire` into the global `Game` engine registry via `mType:register(monster)` [unchained_fire.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
