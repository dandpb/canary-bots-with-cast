# Scrapper

## Overview
Component package under `monster/quests/svargrond_arena/scrapper` containing 10 files (`avalanche.lua`..`the_hag.lua`).

## Interface
- `Game.createMonsterType("Avalanche")` and `mType:register(monster)` [avalanche.lua:Game.createMonsterType]
- `Game.createMonsterType("Drasilla")` and `mType:register(monster)` [drasilla.lua:Game.createMonsterType]
- `Game.createMonsterType("Grimgor Guteater")` and `mType:register(monster)` [grimgor_guteater.lua:Game.createMonsterType]
- `Game.createMonsterType("Kreebosh the Exile")` and `mType:register(monster)` [kreebosh_the_exile.lua:Game.createMonsterType]
- `Game.createMonsterType("Slim")` and `mType:register(monster)` [slim.lua:Game.createMonsterType]
- `Game.createMonsterType("Spirit of Earth")` and `mType:register(monster)` [spirit_of_earth.lua:Game.createMonsterType]
- `Game.createMonsterType("Spirit of Fire")` and `mType:register(monster)` [spirit_of_fire.lua:Game.createMonsterType]
- `Game.createMonsterType("Spirit of Water")` and `mType:register(monster)` [spirit_of_water.lua:Game.createMonsterType]
- `Game.createMonsterType("The Dark Dancer")` and `mType:register(monster)` [the_dark_dancer.lua:Game.createMonsterType]
- `Game.createMonsterType("The Hag")` and `mType:register(monster)` [the_hag.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [avalanche.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [drasilla.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [grimgor_guteater.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [kreebosh_the_exile.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [slim.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [spirit_of_earth.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [spirit_of_fire.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [spirit_of_water.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_dark_dancer.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_hag.lua:monster.flags]

## Side Effects
- Registers monster type `Avalanche` into the global `Game` engine registry via `mType:register(monster)` [avalanche.lua:mType:register]
- Registers monster type `Drasilla` into the global `Game` engine registry via `mType:register(monster)` [drasilla.lua:mType:register]
- Registers monster type `Grimgor Guteater` into the global `Game` engine registry via `mType:register(monster)` [grimgor_guteater.lua:mType:register]
- Registers monster type `Kreebosh the Exile` into the global `Game` engine registry via `mType:register(monster)` [kreebosh_the_exile.lua:mType:register]
- Registers monster type `Slim` into the global `Game` engine registry via `mType:register(monster)` [slim.lua:mType:register]
- Registers monster type `Spirit of Earth` into the global `Game` engine registry via `mType:register(monster)` [spirit_of_earth.lua:mType:register]
- Registers monster type `Spirit of Fire` into the global `Game` engine registry via `mType:register(monster)` [spirit_of_fire.lua:mType:register]
- Registers monster type `Spirit of Water` into the global `Game` engine registry via `mType:register(monster)` [spirit_of_water.lua:mType:register]
- Registers monster type `The Dark Dancer` into the global `Game` engine registry via `mType:register(monster)` [the_dark_dancer.lua:mType:register]
- Registers monster type `The Hag` into the global `Game` engine registry via `mType:register(monster)` [the_hag.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
