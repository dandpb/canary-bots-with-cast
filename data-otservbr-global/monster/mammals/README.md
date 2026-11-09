# Mammals

## Overview
Component package under `monster/mammals` containing 80 files (`badger.lua`..`yeti.lua`).

## Interface
- Defines 80 script/configuration files (`badger.lua` through `yeti.lua`) [badger.lua]
- `Game.createMonsterType("Badger")` and `mType:register(monster)` [badger.lua:Game.createMonsterType]
- `Game.createMonsterType("Bat")` and `mType:register(monster)` [bat.lua:Game.createMonsterType]
- `Game.createMonsterType("Bear")` and `mType:register(monster)` [bear.lua:Game.createMonsterType]
- `Game.createMonsterType("Black Sheep")` and `mType:register(monster)` [black_sheep.lua:Game.createMonsterType]
- `Game.createMonsterType("Boar")` and `mType:register(monster)` [boar.lua:Game.createMonsterType]
- `Game.createMonsterType("Brown Horse")` and `mType:register(monster)` [brown_horse.lua:Game.createMonsterType]
- `Game.createMonsterType("Cat")` and `mType:register(monster)` [cat.lua:Game.createMonsterType]
- `Game.createMonsterType("Cave Rat")` and `mType:register(monster)` [cave_rat.lua:Game.createMonsterType]
- `Game.createMonsterType("Clomp")` and `mType:register(monster)` [clomp.lua:Game.createMonsterType]
- `Game.createMonsterType("Crystal Wolf")` and `mType:register(monster)` [crystal_wolf.lua:Game.createMonsterType]
- `Game.createMonsterType("Deer")` and `mType:register(monster)` [deer.lua:Game.createMonsterType]
- `Game.createMonsterType("Desperate White Deer")` and `mType:register(monster)` [desperate_white_deer.lua:Game.createMonsterType]
- `Game.createMonsterType("Dog")` and `mType:register(monster)` [dog.lua:Game.createMonsterType]
- `Game.createMonsterType("Donkey")` and `mType:register(monster)` [donkey.lua:Game.createMonsterType]
- `Game.createMonsterType("Doom Deer")` and `mType:register(monster)` [doom_deer.lua:Game.createMonsterType]
- `Game.createMonsterType("Dromedary")` and `mType:register(monster)` [dromedary.lua:Game.createMonsterType]
- `Game.createMonsterType("Elephant")` and `mType:register(monster)` [elephant.lua:Game.createMonsterType]
- `Game.createMonsterType("Enraged Squirrel")` and `mType:register(monster)` [enraged_squirrel.lua:Game.createMonsterType]
- `Game.createMonsterType("Enraged White Deer")` and `mType:register(monster)` [enraged_white_deer.lua:Game.createMonsterType]
- `Game.createMonsterType("Evil Sheep")` and `mType:register(monster)` [evil_sheep.lua:Game.createMonsterType]
- `Game.createMonsterType("Evil Sheep Lord")` and `mType:register(monster)` [evil_sheep_lord.lua:Game.createMonsterType]
- `Game.createMonsterType("Exotic Bat")` and `mType:register(monster)` [exotic_bat.lua:Game.createMonsterType]
- `Game.createMonsterType("Fox")` and `mType:register(monster)` [fox.lua:Game.createMonsterType]
- `Game.createMonsterType("Ghost Wolf")` and `mType:register(monster)` [ghost_wolf.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [badger.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [badger.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bat.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bat.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bear.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bear.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [black_sheep.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [black_sheep.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [boar.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [boar.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [brown_horse.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brown_horse.lua:monster.flags]

## Side Effects
- Registers monster type `Badger` into the global `Game` engine registry via `mType:register(monster)` [badger.lua:mType:register]
- Registers monster type `Bat` into the global `Game` engine registry via `mType:register(monster)` [bat.lua:mType:register]
- Registers monster type `Bear` into the global `Game` engine registry via `mType:register(monster)` [bear.lua:mType:register]
- Registers monster type `Black Sheep` into the global `Game` engine registry via `mType:register(monster)` [black_sheep.lua:mType:register]
- Registers monster type `Boar` into the global `Game` engine registry via `mType:register(monster)` [boar.lua:mType:register]
- Registers monster type `Brown Horse` into the global `Game` engine registry via `mType:register(monster)` [brown_horse.lua:mType:register]
- Registers monster type `Cat` into the global `Game` engine registry via `mType:register(monster)` [cat.lua:mType:register]
- Registers monster type `Cave Rat` into the global `Game` engine registry via `mType:register(monster)` [cave_rat.lua:mType:register]
- Registers monster type `Clomp` into the global `Game` engine registry via `mType:register(monster)` [clomp.lua:mType:register]
- Registers monster type `Crystal Wolf` into the global `Game` engine registry via `mType:register(monster)` [crystal_wolf.lua:mType:register]
- Registers monster type `Deer` into the global `Game` engine registry via `mType:register(monster)` [deer.lua:mType:register]
- Registers monster type `Desperate White Deer` into the global `Game` engine registry via `mType:register(monster)` [desperate_white_deer.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
