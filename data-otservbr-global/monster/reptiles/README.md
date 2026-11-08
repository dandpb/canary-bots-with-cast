# Reptiles

## Overview
Component package under `monster/reptiles` containing 42 files (`adult_goanna.lua`..`young_sea_serpent.lua`).

## Interface
- Defines 42 script/configuration files (`adult_goanna.lua` through `young_sea_serpent.lua`) [adult_goanna.lua]
- `Game.createMonsterType("Adult Goanna")` and `mType:register(monster)` [adult_goanna.lua:Game.createMonsterType]
- `Game.createMonsterType("Boar Man")` and `mType:register(monster)` [boar_man.lua:Game.createMonsterType]
- `Game.createMonsterType("Carnivostrich")` and `mType:register(monster)` [carnivostrich.lua:Game.createMonsterType]
- `Game.createMonsterType("Cobra")` and `mType:register(monster)` [cobra.lua:Game.createMonsterType]
- `Game.createMonsterType("Corrupt Naga")` and `mType:register(monster)` [corrupt_naga.lua:Game.createMonsterType]
- `Game.createMonsterType("Crape Man")` and `mType:register(monster)` [crape_man.lua:Game.createMonsterType]
- `Game.createMonsterType("Crocodile")` and `mType:register(monster)` [crocodile.lua:Game.createMonsterType]
- `Game.createMonsterType("Dreadmaw")` and `mType:register(monster)` [dreadmaw.lua:Game.createMonsterType]
- `Game.createMonsterType("Emerald Tortoise")` and `mType:register(monster)` [emerald_tortoise.lua:Game.createMonsterType]
- `Game.createMonsterType("Fungosaurus")` and `mType:register(monster)` [fungosaurus.lua:Game.createMonsterType]
- `Game.createMonsterType("Harpy")` and `mType:register(monster)` [harpy.lua:Game.createMonsterType]
- `Game.createMonsterType("Killer Caiman")` and `mType:register(monster)` [killer_caiman.lua:Game.createMonsterType]
- `Game.createMonsterType("Liodile")` and `mType:register(monster)` [liodile.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard Chosen")` and `mType:register(monster)` [lizard_chosen.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard Dragon Priest")` and `mType:register(monster)` [lizard_dragon_priest.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard High Guard")` and `mType:register(monster)` [lizard_high_guard.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard Legionnaire")` and `mType:register(monster)` [lizard_legionnaire.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard Magistratus")` and `mType:register(monster)` [lizard_magistratus.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard Noble")` and `mType:register(monster)` [lizard_noble.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard Sentinel")` and `mType:register(monster)` [lizard_sentinel.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard Snakecharmer")` and `mType:register(monster)` [lizard_snakecharmer.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard Templar")` and `mType:register(monster)` [lizard_templar.lua:Game.createMonsterType]
- `Game.createMonsterType("Lizard Zaogun")` and `mType:register(monster)` [lizard_zaogun.lua:Game.createMonsterType]
- `Game.createMonsterType("Mantosaurus")` and `mType:register(monster)` [mantosaurus.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [adult_goanna.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [adult_goanna.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [boar_man.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [boar_man.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [carnivostrich.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [carnivostrich.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [cobra.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cobra.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [corrupt_naga.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [crape_man.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [crape_man.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [crocodile.lua:monster.Bestiary]

## Side Effects
- Registers monster type `Adult Goanna` into the global `Game` engine registry via `mType:register(monster)` [adult_goanna.lua:mType:register]
- Registers monster type `Boar Man` into the global `Game` engine registry via `mType:register(monster)` [boar_man.lua:mType:register]
- Registers monster type `Carnivostrich` into the global `Game` engine registry via `mType:register(monster)` [carnivostrich.lua:mType:register]
- Registers monster type `Cobra` into the global `Game` engine registry via `mType:register(monster)` [cobra.lua:mType:register]
- Registers monster type `Corrupt Naga` into the global `Game` engine registry via `mType:register(monster)` [corrupt_naga.lua:mType:register]
- Registers monster type `Crape Man` into the global `Game` engine registry via `mType:register(monster)` [crape_man.lua:mType:register]
- Registers monster type `Crocodile` into the global `Game` engine registry via `mType:register(monster)` [crocodile.lua:mType:register]
- Registers monster type `Dreadmaw` into the global `Game` engine registry via `mType:register(monster)` [dreadmaw.lua:mType:register]
- Registers monster type `Emerald Tortoise` into the global `Game` engine registry via `mType:register(monster)` [emerald_tortoise.lua:mType:register]
- Registers monster type `Fungosaurus` into the global `Game` engine registry via `mType:register(monster)` [fungosaurus.lua:mType:register]
- Registers monster type `Harpy` into the global `Game` engine registry via `mType:register(monster)` [harpy.lua:mType:register]
- Registers monster type `Killer Caiman` into the global `Game` engine registry via `mType:register(monster)` [killer_caiman.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
