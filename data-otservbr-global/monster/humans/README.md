# Humans

## Overview
Component package under `monster/humans` containing 75 files (`acolyte_of_darkness.lua`..`witch.lua`).

## Interface
- Defines 75 script/configuration files (`acolyte_of_darkness.lua` through `witch.lua`) [acolyte_of_darkness.lua]
- `Game.createMonsterType("Acolyte of Darkness")` and `mType:register(monster)` [acolyte_of_darkness.lua:Game.createMonsterType]
- `Game.createMonsterType("Acolyte of the Cult")` and `mType:register(monster)` [acolyte_of_the_cult.lua:Game.createMonsterType]
- `Game.createMonsterType("Adept of the Cult")` and `mType:register(monster)` [adept_of_the_cult.lua:Game.createMonsterType]
- `Game.createMonsterType("Adventurer")` and `mType:register(monster)` [adventurer.lua:Game.createMonsterType]
- `Game.createMonsterType("Amazon")` and `mType:register(monster)` [amazon.lua:Game.createMonsterType]
- `Game.createMonsterType("Angry Adventurer")` and `mType:register(monster)` [angry_adventurer.lua:Game.createMonsterType]
- `Game.createMonsterType("Assassin")` and `mType:register(monster)` [assassin.lua:Game.createMonsterType]
- `Game.createMonsterType("Bandit")` and `mType:register(monster)` [bandit.lua:Game.createMonsterType]
- `Game.createMonsterType("Barbarian Bloodwalker")` and `mType:register(monster)` [barbarian_bloodwalker.lua:Game.createMonsterType]
- `Game.createMonsterType("Barbarian Brutetamer")` and `mType:register(monster)` [barbarian_brutetamer.lua:Game.createMonsterType]
- `Game.createMonsterType("Barbarian Headsplitter")` and `mType:register(monster)` [barbarian_headsplitter.lua:Game.createMonsterType]
- `Game.createMonsterType("Barbarian Skullhunter")` and `mType:register(monster)` [barbarian_skullhunter.lua:Game.createMonsterType]
- `Game.createMonsterType("Black Sphinx Acolyte")` and `mType:register(monster)` [black_sphinx_acolyte.lua:Game.createMonsterType]
- `Game.createMonsterType("Blood Hand")` and `mType:register(monster)` [blood_hand.lua:Game.createMonsterType]
- `Game.createMonsterType("Blood Priest")` and `mType:register(monster)` [blood_priest.lua:Game.createMonsterType]
- `Game.createMonsterType("Burning Gladiator")` and `mType:register(monster)` [burning_gladiator.lua:Game.createMonsterType]
- `Game.createMonsterType("Carnisylvan Sapling")` and `mType:register(monster)` [carnisylvan_sapling.lua:Game.createMonsterType]
- `Game.createMonsterType("Cobra Assassin")` and `mType:register(monster)` [cobra_assassin.lua:Game.createMonsterType]
- `Game.createMonsterType("Cobra Scout")` and `mType:register(monster)` [cobra_scout.lua:Game.createMonsterType]
- `Game.createMonsterType("Cobra Vizier")` and `mType:register(monster)` [cobra_vizier.lua:Game.createMonsterType]
- `Game.createMonsterType("Crazed Beggar")` and `mType:register(monster)` [crazed_beggar.lua:Game.createMonsterType]
- `Game.createMonsterType("Crypt Defiler")` and `mType:register(monster)` [crypt_defiler.lua:Game.createMonsterType]
- `Game.createMonsterType("Dark Apprentice")` and `mType:register(monster)` [dark_apprentice.lua:Game.createMonsterType]
- `Game.createMonsterType("Dark Carnisylvan")` and `mType:register(monster)` [dark_carnisylvan.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [acolyte_of_darkness.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [acolyte_of_darkness.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [acolyte_of_the_cult.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [acolyte_of_the_cult.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [adept_of_the_cult.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [adept_of_the_cult.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [adventurer.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [adventurer.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [amazon.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [amazon.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [angry_adventurer.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [assassin.lua:monster.Bestiary]

## Side Effects
- Registers monster type `Acolyte of Darkness` into the global `Game` engine registry via `mType:register(monster)` [acolyte_of_darkness.lua:mType:register]
- Registers monster type `Acolyte of the Cult` into the global `Game` engine registry via `mType:register(monster)` [acolyte_of_the_cult.lua:mType:register]
- Registers monster type `Adept of the Cult` into the global `Game` engine registry via `mType:register(monster)` [adept_of_the_cult.lua:mType:register]
- Registers monster type `Adventurer` into the global `Game` engine registry via `mType:register(monster)` [adventurer.lua:mType:register]
- Registers monster type `Amazon` into the global `Game` engine registry via `mType:register(monster)` [amazon.lua:mType:register]
- Registers monster type `Angry Adventurer` into the global `Game` engine registry via `mType:register(monster)` [angry_adventurer.lua:mType:register]
- Registers monster type `Assassin` into the global `Game` engine registry via `mType:register(monster)` [assassin.lua:mType:register]
- Registers monster type `Bandit` into the global `Game` engine registry via `mType:register(monster)` [bandit.lua:mType:register]
- Registers monster type `Barbarian Bloodwalker` into the global `Game` engine registry via `mType:register(monster)` [barbarian_bloodwalker.lua:mType:register]
- Registers monster type `Barbarian Brutetamer` into the global `Game` engine registry via `mType:register(monster)` [barbarian_brutetamer.lua:mType:register]
- Registers monster type `Barbarian Headsplitter` into the global `Game` engine registry via `mType:register(monster)` [barbarian_headsplitter.lua:mType:register]
- Registers monster type `Barbarian Skullhunter` into the global `Game` engine registry via `mType:register(monster)` [barbarian_skullhunter.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
