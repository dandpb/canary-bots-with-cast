# Lycanthropes

## Overview
Component package under `monster/lycanthropes` containing 15 files (`cunning_werepanther.lua`..`white_weretiger.lua`).

## Interface
- `Game.createMonsterType("Cunning Werepanther")` and `mType:register(monster)` [cunning_werepanther.lua:Game.createMonsterType]
- `Game.createMonsterType("Feral Werecrocodile")` and `mType:register(monster)` [feral_werecrocodile.lua:Game.createMonsterType]
- `Game.createMonsterType("Werebadger")` and `mType:register(monster)` [werebadger.lua:Game.createMonsterType]
- `Game.createMonsterType("Werebear")` and `mType:register(monster)` [werebear.lua:Game.createMonsterType]
- `Game.createMonsterType("Wereboar")` and `mType:register(monster)` [wereboar.lua:Game.createMonsterType]
- `Game.createMonsterType("Werecrocodile")` and `mType:register(monster)` [werecrocodile.lua:Game.createMonsterType]
- `Game.createMonsterType("Werefox")` and `mType:register(monster)` [werefox.lua:Game.createMonsterType]
- `Game.createMonsterType("Werehyaena")` and `mType:register(monster)` [werehyaena.lua:Game.createMonsterType]
- `Game.createMonsterType("Werehyaena Shaman")` and `mType:register(monster)` [werehyaena_shaman.lua:Game.createMonsterType]
- `Game.createMonsterType("Werelion")` and `mType:register(monster)` [werelion.lua:Game.createMonsterType]
- `Game.createMonsterType("Werelioness")` and `mType:register(monster)` [werelioness.lua:Game.createMonsterType]
- `Game.createMonsterType("Werepanther")` and `mType:register(monster)` [werepanther.lua:Game.createMonsterType]
- `Game.createMonsterType("Weretiger")` and `mType:register(monster)` [weretiger.lua:Game.createMonsterType]
- `Game.createMonsterType("Werewolf")` and `mType:register(monster)` [werewolf.lua:Game.createMonsterType]
- `Game.createMonsterType("White Weretiger")` and `mType:register(monster)` [white_weretiger.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [cunning_werepanther.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cunning_werepanther.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [feral_werecrocodile.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [feral_werecrocodile.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [werebadger.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [werebadger.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [werebear.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [werebear.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [wereboar.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [wereboar.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [werecrocodile.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [werecrocodile.lua:monster.flags]

## Side Effects
- Registers monster type `Cunning Werepanther` into the global `Game` engine registry via `mType:register(monster)` [cunning_werepanther.lua:mType:register]
- Registers monster type `Feral Werecrocodile` into the global `Game` engine registry via `mType:register(monster)` [feral_werecrocodile.lua:mType:register]
- Registers monster type `Werebadger` into the global `Game` engine registry via `mType:register(monster)` [werebadger.lua:mType:register]
- Registers monster type `Werebear` into the global `Game` engine registry via `mType:register(monster)` [werebear.lua:mType:register]
- Registers monster type `Wereboar` into the global `Game` engine registry via `mType:register(monster)` [wereboar.lua:mType:register]
- Registers monster type `Werecrocodile` into the global `Game` engine registry via `mType:register(monster)` [werecrocodile.lua:mType:register]
- Registers monster type `Werefox` into the global `Game` engine registry via `mType:register(monster)` [werefox.lua:mType:register]
- Registers monster type `Werehyaena` into the global `Game` engine registry via `mType:register(monster)` [werehyaena.lua:mType:register]
- Registers monster type `Werehyaena Shaman` into the global `Game` engine registry via `mType:register(monster)` [werehyaena_shaman.lua:mType:register]
- Registers monster type `Werelion` into the global `Game` engine registry via `mType:register(monster)` [werelion.lua:mType:register]
- Registers monster type `Werelioness` into the global `Game` engine registry via `mType:register(monster)` [werelioness.lua:mType:register]
- Registers monster type `Werepanther` into the global `Game` engine registry via `mType:register(monster)` [werepanther.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
