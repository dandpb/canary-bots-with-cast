# Killing In The Name Of

## Overview
Component package under `monster/quests/killing_in_the_name_of` containing 30 files (`bretzecutioner.lua`..`zanakeph.lua`).

## Interface
- Defines 30 script/configuration files (`bretzecutioner.lua` through `zanakeph.lua`) [bretzecutioner.lua]
- `Game.createMonsterType("Bretzecutioner")` and `mType:register(monster)` [bretzecutioner.lua:Game.createMonsterType]
- `Game.createMonsterType("Bruise Payne")` and `mType:register(monster)` [bruise_payne.lua:Game.createMonsterType]
- `Game.createMonsterType("Deathbine")` and `mType:register(monster)` [deathbine.lua:Game.createMonsterType]
- `Game.createMonsterType("Demodras")` and `mType:register(monster)` [demodras.lua:Game.createMonsterType]
- `Game.createMonsterType("Esmeralda")` and `mType:register(monster)` [esmeralda.lua:Game.createMonsterType]
- `Game.createMonsterType("Ethershreck")` and `mType:register(monster)` [ethershreck.lua:Game.createMonsterType]
- `Game.createMonsterType("Fazzrah")` and `mType:register(monster)` [fazzrah.lua:Game.createMonsterType]
- `Game.createMonsterType("Flameborn")` and `mType:register(monster)` [flameborn.lua:Game.createMonsterType]
- `Game.createMonsterType("Fleshcrawler")` and `mType:register(monster)` [fleshcrawler.lua:Game.createMonsterType]
- `Game.createMonsterType("Gorgo")` and `mType:register(monster)` [gorgo.lua:Game.createMonsterType]
- `Game.createMonsterType("Hemming")` and `mType:register(monster)` [hemming.lua:Game.createMonsterType]
- `Game.createMonsterType("Hide")` and `mType:register(monster)` [hide.lua:Game.createMonsterType]
- `Game.createMonsterType("Kerberos")` and `mType:register(monster)` [kerberos.lua:Game.createMonsterType]
- `Game.createMonsterType("Leviathan")` and `mType:register(monster)` [leviathan.lua:Game.createMonsterType]
- `Game.createMonsterType("Paiz the Pauperizer")` and `mType:register(monster)` [paiz_the_pauperizer.lua:Game.createMonsterType]
- `Game.createMonsterType("Ribstride")` and `mType:register(monster)` [ribstride.lua:Game.createMonsterType]
- `Game.createMonsterType("Shardhead")` and `mType:register(monster)` [shardhead.lua:Game.createMonsterType]
- `Game.createMonsterType("Stonecracker")` and `mType:register(monster)` [stonecracker.lua:Game.createMonsterType]
- `Game.createMonsterType("Sulphur Scuttler")` and `mType:register(monster)` [sulphur_scuttler.lua:Game.createMonsterType]
- `Game.createMonsterType("The Bloodtusk")` and `mType:register(monster)` [the_bloodtusk.lua:Game.createMonsterType]
- `Game.createMonsterType("The Bloodweb")` and `mType:register(monster)` [the_bloodweb.lua:Game.createMonsterType]
- `Game.createMonsterType("The Many")` and `mType:register(monster)` [the_many.lua:Game.createMonsterType]
- `Game.createMonsterType("The Noxious Spawn")` and `mType:register(monster)` [the_noxious_spawn.lua:Game.createMonsterType]
- `Game.createMonsterType("The Old Widow")` and `mType:register(monster)` [the_old_widow.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bretzecutioner.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bruise_payne.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [deathbine.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [demodras.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [esmeralda.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ethershreck.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fazzrah.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [flameborn.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fleshcrawler.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [gorgo.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [hemming.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [hide.lua:monster.flags]

## Side Effects
- Registers monster type `Bretzecutioner` into the global `Game` engine registry via `mType:register(monster)` [bretzecutioner.lua:mType:register]
- Registers monster type `Bruise Payne` into the global `Game` engine registry via `mType:register(monster)` [bruise_payne.lua:mType:register]
- Registers monster type `Deathbine` into the global `Game` engine registry via `mType:register(monster)` [deathbine.lua:mType:register]
- Registers monster type `Demodras` into the global `Game` engine registry via `mType:register(monster)` [demodras.lua:mType:register]
- Registers monster type `Esmeralda` into the global `Game` engine registry via `mType:register(monster)` [esmeralda.lua:mType:register]
- Registers monster type `Ethershreck` into the global `Game` engine registry via `mType:register(monster)` [ethershreck.lua:mType:register]
- Registers monster type `Fazzrah` into the global `Game` engine registry via `mType:register(monster)` [fazzrah.lua:mType:register]
- Registers monster type `Flameborn` into the global `Game` engine registry via `mType:register(monster)` [flameborn.lua:mType:register]
- Registers monster type `Fleshcrawler` into the global `Game` engine registry via `mType:register(monster)` [fleshcrawler.lua:mType:register]
- Registers monster type `Gorgo` into the global `Game` engine registry via `mType:register(monster)` [gorgo.lua:mType:register]
- Registers monster type `Hemming` into the global `Game` engine registry via `mType:register(monster)` [hemming.lua:mType:register]
- Registers monster type `Hide` into the global `Game` engine registry via `mType:register(monster)` [hide.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
