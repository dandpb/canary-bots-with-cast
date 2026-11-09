# Pits Of Inferno

## Overview
Component package under `monster/quests/pits_of_inferno` containing 9 files (`countess_sorrow.lua`..`the_plasmother.lua`).

## Interface
- `Game.createMonsterType("Countess Sorrow")` and `mType:register(monster)` [countess_sorrow.lua:Game.createMonsterType]
- `Game.createMonsterType("Demon Goblin")` and `mType:register(monster)` [demon_goblin.lua:Game.createMonsterType]
- `Game.createMonsterType("Dracola")` and `mType:register(monster)` [dracola.lua:Game.createMonsterType]
- `Game.createMonsterType("Flamethrower")` and `mType:register(monster)` [flamethrower.lua:Game.createMonsterType]
- `Game.createMonsterType("Massacre")` and `mType:register(monster)` [massacre.lua:Game.createMonsterType]
- `Game.createMonsterType("Mr. Punish")` and `mType:register(monster)` [mr._punish.lua:Game.createMonsterType]
- `Game.createMonsterType("The Handmaiden")` and `mType:register(monster)` [the_handmaiden.lua:Game.createMonsterType]
- `Game.createMonsterType("The Imperor")` and `mType:register(monster)` [the_imperor.lua:Game.createMonsterType]
- `Game.createMonsterType("The Plasmother")` and `mType:register(monster)` [the_plasmother.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [countess_sorrow.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [demon_goblin.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dracola.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [flamethrower.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [massacre.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mr._punish.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_handmaiden.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_imperor.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_plasmother.lua:monster.flags]

## Side Effects
- Registers monster type `Countess Sorrow` into the global `Game` engine registry via `mType:register(monster)` [countess_sorrow.lua:mType:register]
- Registers monster type `Demon Goblin` into the global `Game` engine registry via `mType:register(monster)` [demon_goblin.lua:mType:register]
- Registers monster type `Dracola` into the global `Game` engine registry via `mType:register(monster)` [dracola.lua:mType:register]
- Registers monster type `Flamethrower` into the global `Game` engine registry via `mType:register(monster)` [flamethrower.lua:mType:register]
- Registers monster type `Massacre` into the global `Game` engine registry via `mType:register(monster)` [massacre.lua:mType:register]
- Registers monster type `Mr. Punish` into the global `Game` engine registry via `mType:register(monster)` [mr._punish.lua:mType:register]
- Registers monster type `The Handmaiden` into the global `Game` engine registry via `mType:register(monster)` [the_handmaiden.lua:mType:register]
- Registers monster type `The Imperor` into the global `Game` engine registry via `mType:register(monster)` [the_imperor.lua:mType:register]
- Registers monster type `The Plasmother` into the global `Game` engine registry via `mType:register(monster)` [the_plasmother.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
