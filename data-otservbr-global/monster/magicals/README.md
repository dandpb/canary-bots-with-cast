# Magicals

## Overview
Component package under `monster/magicals` containing 64 files (`animated_feather.lua`..`weakened_frazzlemaw.lua`).

## Interface
- Defines 64 script/configuration files (`animated_feather.lua` through `weakened_frazzlemaw.lua`) [animated_feather.lua]
- `Game.createMonsterType("Animated Feather")` and `mType:register(monster)` [animated_feather.lua:Game.createMonsterType]
- `Game.createMonsterType("Arachnophobica")` and `mType:register(monster)` [arachnophobica.lua:Game.createMonsterType]
- `Game.createMonsterType("Armadile")` and `mType:register(monster)` [armadile.lua:Game.createMonsterType]
- `Game.createMonsterType("Bashmu")` and `mType:register(monster)` [bashmu.lua:Game.createMonsterType]
- `Game.createMonsterType("Blue Djinn")` and `mType:register(monster)` [blue_djinn.lua:Game.createMonsterType]
- `Game.createMonsterType("Bog Raider")` and `mType:register(monster)` [bog_raider.lua:Game.createMonsterType]
- `Game.createMonsterType("Bonelord")` and `mType:register(monster)` [bonelord.lua:Game.createMonsterType]
- `Game.createMonsterType("Brain Squid")` and `mType:register(monster)` [brain_squid.lua:Game.createMonsterType]
- `Game.createMonsterType("Braindeath")` and `mType:register(monster)` [braindeath.lua:Game.createMonsterType]
- `Game.createMonsterType("Burning Book")` and `mType:register(monster)` [burning_book.lua:Game.createMonsterType]
- `Game.createMonsterType("Candy Horror")` and `mType:register(monster)` [candy_horror.lua:Game.createMonsterType]
- `Game.createMonsterType("Choking Fear")` and `mType:register(monster)` [choking_fear.lua:Game.createMonsterType]
- `Game.createMonsterType("Crypt Warden")` and `mType:register(monster)` [crypt_warden.lua:Game.createMonsterType]
- `Game.createMonsterType("Crystalcrusher")` and `mType:register(monster)` [crystalcrusher.lua:Game.createMonsterType]
- `Game.createMonsterType("Cursed Book")` and `mType:register(monster)` [cursed_book.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragonling")` and `mType:register(monster)` [dragonling.lua:Game.createMonsterType]
- `Game.createMonsterType("Efreet")` and `mType:register(monster)` [efreet.lua:Game.createMonsterType]
- `Game.createMonsterType("Elder Bonelord")` and `mType:register(monster)` [elder_bonelord.lua:Game.createMonsterType]
- `Game.createMonsterType("Energetic Book")` and `mType:register(monster)` [energetic_book.lua:Game.createMonsterType]
- `Game.createMonsterType("Energuardian of Tales")` and `mType:register(monster)` [energuardian_of_tales.lua:Game.createMonsterType]
- `Game.createMonsterType("Enfeebled Silencer")` and `mType:register(monster)` [enfeebled_silencer.lua:Game.createMonsterType]
- `Game.createMonsterType("Fahim the Wise")` and `mType:register(monster)` [fahim_the_wise.lua:Game.createMonsterType]
- `Game.createMonsterType("Feral Sphinx")` and `mType:register(monster)` [feral_sphinx.lua:Game.createMonsterType]
- `Game.createMonsterType("Feversleep")` and `mType:register(monster)` [feversleep.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [animated_feather.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_feather.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [arachnophobica.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [arachnophobica.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [armadile.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [armadile.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bashmu.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bashmu.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [blue_djinn.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [blue_djinn.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bog_raider.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bog_raider.lua:monster.flags]

## Side Effects
- Registers monster type `Animated Feather` into the global `Game` engine registry via `mType:register(monster)` [animated_feather.lua:mType:register]
- Registers monster type `Arachnophobica` into the global `Game` engine registry via `mType:register(monster)` [arachnophobica.lua:mType:register]
- Registers monster type `Armadile` into the global `Game` engine registry via `mType:register(monster)` [armadile.lua:mType:register]
- Registers monster type `Bashmu` into the global `Game` engine registry via `mType:register(monster)` [bashmu.lua:mType:register]
- Registers monster type `Blue Djinn` into the global `Game` engine registry via `mType:register(monster)` [blue_djinn.lua:mType:register]
- Registers monster type `Bog Raider` into the global `Game` engine registry via `mType:register(monster)` [bog_raider.lua:mType:register]
- Registers monster type `Bonelord` into the global `Game` engine registry via `mType:register(monster)` [bonelord.lua:mType:register]
- Registers monster type `Brain Squid` into the global `Game` engine registry via `mType:register(monster)` [brain_squid.lua:mType:register]
- Registers monster type `Braindeath` into the global `Game` engine registry via `mType:register(monster)` [braindeath.lua:mType:register]
- Registers monster type `Burning Book` into the global `Game` engine registry via `mType:register(monster)` [burning_book.lua:mType:register]
- Registers monster type `Candy Horror` into the global `Game` engine registry via `mType:register(monster)` [candy_horror.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [candy_horror.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
