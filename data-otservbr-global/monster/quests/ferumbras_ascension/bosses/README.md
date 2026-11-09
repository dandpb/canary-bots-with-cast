# Bosses

## Overview
Component package under `monster/quests/ferumbras_ascension/bosses` containing 19 files (`ascending_ferumbras.lua`..`zamulosh3.lua`).

## Interface
- `Game.createMonsterType("Ascending Ferumbras")` and `mType:register(monster)` [ascending_ferumbras.lua:Game.createMonsterType]
- `Game.createMonsterType("Death Dragon")` and `mType:register(monster)` [death_dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Destabilized Ferumbras")` and `mType:register(monster)` [destabilized_ferumbras.lua:Game.createMonsterType]
- `Game.createMonsterType("Enraged Soul")` and `mType:register(monster)` [enraged_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Ferumbras Mortal Shell")` and `mType:register(monster)` [ferumbras_mortal_shell.lua:Game.createMonsterType]
- `Game.createMonsterType("Ferumbras Soul Splinter")` and `mType:register(monster)` [ferumbras_soul_splinter.lua:Game.createMonsterType]
- `Game.createMonsterType("Mazoran")` and `mType:register(monster)` [mazoran.lua:Game.createMonsterType]
- `Game.createMonsterType("Plagirath")` and `mType:register(monster)` [plagirath.lua:Game.createMonsterType]
- `Game.createMonsterType("Ragiaz")` and `mType:register(monster)` [ragiaz.lua:Game.createMonsterType]
- `Game.createMonsterType("Razzagorn")` and `mType:register(monster)` [razzagorn.lua:Game.createMonsterType]
- `Game.createMonsterType("Redeemed Soul")` and `mType:register(monster)` [redeemed_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Shulgrax")` and `mType:register(monster)` [shulgrax.lua:Game.createMonsterType]
- `Game.createMonsterType("Sin Devourer")` and `mType:register(monster)` [sin_devourer.lua:Game.createMonsterType]
- `Game.createMonsterType("Tarbaz")` and `mType:register(monster)` [tarbaz.lua:Game.createMonsterType]
- `Game.createMonsterType("The Lord of the Lice")` and `mType:register(monster)` [the_lord_of_the_lice.lua:Game.createMonsterType]
- `Game.createMonsterType("The Shatterer")` and `mType:register(monster)` [the_shatterer.lua:Game.createMonsterType]
- `Game.createMonsterType("Zamulosh")` and `mType:register(monster)` [zamulosh.lua:Game.createMonsterType]
- `Game.createMonsterType("Zamulosh2")` and `mType:register(monster)` [zamulosh2.lua:Game.createMonsterType]
- `Game.createMonsterType("Zamulosh3")` and `mType:register(monster)` [zamulosh3.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ascending_ferumbras.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [death_dragon.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [destabilized_ferumbras.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [enraged_soul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ferumbras_mortal_shell.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ferumbras_soul_splinter.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mazoran.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [plagirath.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ragiaz.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [razzagorn.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [redeemed_soul.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [redeemed_soul.lua:monster.flags]

## Side Effects
- Registers monster type `Ascending Ferumbras` into the global `Game` engine registry via `mType:register(monster)` [ascending_ferumbras.lua:mType:register]
- Registers monster type `Death Dragon` into the global `Game` engine registry via `mType:register(monster)` [death_dragon.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [death_dragon.lua:monster.events]
- Registers monster type `Destabilized Ferumbras` into the global `Game` engine registry via `mType:register(monster)` [destabilized_ferumbras.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [destabilized_ferumbras.lua:monster.events]
- Registers monster type `Enraged Soul` into the global `Game` engine registry via `mType:register(monster)` [enraged_soul.lua:mType:register]
- Registers monster type `Ferumbras Mortal Shell` into the global `Game` engine registry via `mType:register(monster)` [ferumbras_mortal_shell.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [ferumbras_mortal_shell.lua:monster.events]
- Registers monster type `Ferumbras Soul Splinter` into the global `Game` engine registry via `mType:register(monster)` [ferumbras_soul_splinter.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [ferumbras_soul_splinter.lua:monster.events]
- Registers monster type `Mazoran` into the global `Game` engine registry via `mType:register(monster)` [mazoran.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [mazoran.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
