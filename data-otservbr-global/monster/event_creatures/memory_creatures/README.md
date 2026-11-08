# Memory Creatures

## Overview
Component package under `monster/event_creatures/memory_creatures` containing 24 files (`memory_of_a_banshee.lua`..`memory_of_an_ogre.lua`).

## Interface
- `Game.createMonsterType("Memory of a Banshee")` and `mType:register(monster)` [memory_of_a_banshee.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Book")` and `mType:register(monster)` [memory_of_a_book.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Carnisylvan")` and `mType:register(monster)` [memory_of_a_carnisylvan.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Dwarf")` and `mType:register(monster)` [memory_of_a_dwarf.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Faun")` and `mType:register(monster)` [memory_of_a_faun.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Frazzlemaw")` and `mType:register(monster)` [memory_of_a_frazzlemaw.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Fungus")` and `mType:register(monster)` [memory_of_a_fungus.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Golem")` and `mType:register(monster)` [memory_of_a_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Hero")` and `mType:register(monster)` [memory_of_a_hero.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Hydra")` and `mType:register(monster)` [memory_of_a_hydra.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Lizard")` and `mType:register(monster)` [memory_of_a_lizard.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Mammoth")` and `mType:register(monster)` [memory_of_a_mammoth.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Manticore")` and `mType:register(monster)` [memory_of_a_manticore.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Pirate")` and `mType:register(monster)` [memory_of_a_pirate.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Scarab")` and `mType:register(monster)` [memory_of_a_scarab.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Shaper")` and `mType:register(monster)` [memory_of_a_shaper.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Vampire")` and `mType:register(monster)` [memory_of_a_vampire.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Werelion")` and `mType:register(monster)` [memory_of_a_werelion.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Wolf")` and `mType:register(monster)` [memory_of_a_wolf.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of a Yalahari")` and `mType:register(monster)` [memory_of_a_yalahari.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of an Amazon")` and `mType:register(monster)` [memory_of_an_amazon.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of an Elf")` and `mType:register(monster)` [memory_of_an_elf.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of an Insectoid")` and `mType:register(monster)` [memory_of_an_insectoid.lua:Game.createMonsterType]
- `Game.createMonsterType("Memory of an Ogre")` and `mType:register(monster)` [memory_of_an_ogre.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_banshee.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_book.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_carnisylvan.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_dwarf.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_faun.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_frazzlemaw.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_fungus.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_golem.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_hero.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_hydra.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_lizard.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [memory_of_a_mammoth.lua:monster.flags]

## Side Effects
- Registers monster type `Memory of a Banshee` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_banshee.lua:mType:register]
- Registers monster type `Memory of a Book` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_book.lua:mType:register]
- Registers monster type `Memory of a Carnisylvan` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_carnisylvan.lua:mType:register]
- Registers monster type `Memory of a Dwarf` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_dwarf.lua:mType:register]
- Registers monster type `Memory of a Faun` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_faun.lua:mType:register]
- Registers monster type `Memory of a Frazzlemaw` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_frazzlemaw.lua:mType:register]
- Registers monster type `Memory of a Fungus` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_fungus.lua:mType:register]
- Registers monster type `Memory of a Golem` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_golem.lua:mType:register]
- Registers monster type `Memory of a Hero` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_hero.lua:mType:register]
- Registers monster type `Memory of a Hydra` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_hydra.lua:mType:register]
- Registers monster type `Memory of a Lizard` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_lizard.lua:mType:register]
- Registers monster type `Memory of a Mammoth` into the global `Game` engine registry via `mType:register(monster)` [memory_of_a_mammoth.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
