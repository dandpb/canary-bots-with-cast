# Lovely

## Overview
Component package under `monster/quests/ferumbras_ascension/lovely` containing 8 files (`lovely_deer.lua`..`lovely_yielothax.lua`).

## Interface
- `Game.createMonsterType("Lovely Deer")` and `mType:register(monster)` [lovely_deer.lua:Game.createMonsterType]
- `Game.createMonsterType("Lovely Frazzlemaw")` and `mType:register(monster)` [lovely_frazzlemaw.lua:Game.createMonsterType]
- `Game.createMonsterType("Lovely Polar Bear")` and `mType:register(monster)` [lovely_polar_bear.lua:Game.createMonsterType]
- `Game.createMonsterType("Lovely Rotworm")` and `mType:register(monster)` [lovely_rotworm.lua:Game.createMonsterType]
- `Game.createMonsterType("Lovely Scorpion")` and `mType:register(monster)` [lovely_scorpion.lua:Game.createMonsterType]
- `Game.createMonsterType("Lovely Snake")` and `mType:register(monster)` [lovely_snake.lua:Game.createMonsterType]
- `Game.createMonsterType("Lovely Souleater")` and `mType:register(monster)` [lovely_souleater.lua:Game.createMonsterType]
- `Game.createMonsterType("Lovely Yielothax")` and `mType:register(monster)` [lovely_yielothax.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lovely_deer.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lovely_frazzlemaw.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lovely_polar_bear.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lovely_rotworm.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lovely_scorpion.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lovely_snake.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lovely_souleater.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lovely_yielothax.lua:monster.flags]

## Side Effects
- Registers monster type `Lovely Deer` into the global `Game` engine registry via `mType:register(monster)` [lovely_deer.lua:mType:register]
- Registers monster type `Lovely Frazzlemaw` into the global `Game` engine registry via `mType:register(monster)` [lovely_frazzlemaw.lua:mType:register]
- Registers monster type `Lovely Polar Bear` into the global `Game` engine registry via `mType:register(monster)` [lovely_polar_bear.lua:mType:register]
- Registers monster type `Lovely Rotworm` into the global `Game` engine registry via `mType:register(monster)` [lovely_rotworm.lua:mType:register]
- Registers monster type `Lovely Scorpion` into the global `Game` engine registry via `mType:register(monster)` [lovely_scorpion.lua:mType:register]
- Registers monster type `Lovely Snake` into the global `Game` engine registry via `mType:register(monster)` [lovely_snake.lua:mType:register]
- Registers monster type `Lovely Souleater` into the global `Game` engine registry via `mType:register(monster)` [lovely_souleater.lua:mType:register]
- Registers monster type `Lovely Yielothax` into the global `Game` engine registry via `mType:register(monster)` [lovely_yielothax.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
