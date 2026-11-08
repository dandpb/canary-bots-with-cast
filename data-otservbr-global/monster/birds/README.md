# Birds

## Overview
Component package under `monster/birds` containing 17 files (`agressive_chicken.lua`..`terror_bird.lua`).

## Interface
- `Game.createMonsterType("Agressive Chicken")` and `mType:register(monster)` [agressive_chicken.lua:Game.createMonsterType]
- `Game.createMonsterType("Agrestic Chicken")` and `mType:register(monster)` [agrestic_chicken.lua:Game.createMonsterType]
- `Game.createMonsterType("Berserker Chicken")` and `mType:register(monster)` [berserker_chicken.lua:Game.createMonsterType]
- `Game.createMonsterType("Cave Parrot")` and `mType:register(monster)` [cave_parrot.lua:Game.createMonsterType]
- `Game.createMonsterType("Chicken")` and `mType:register(monster)` [chicken.lua:Game.createMonsterType]
- `Game.createMonsterType("Demon Parrot")` and `mType:register(monster)` [demon_parrot.lua:Game.createMonsterType]
- `Game.createMonsterType("Dire Penguin")` and `mType:register(monster)` [dire_penguin.lua:Game.createMonsterType]
- `Game.createMonsterType("Flamingo")` and `mType:register(monster)` [flamingo.lua:Game.createMonsterType]
- `Game.createMonsterType("Headpecker")` and `mType:register(monster)` [headpecker.lua:Game.createMonsterType]
- `Game.createMonsterType("Jungle Moa")` and `mType:register(monster)` [jungle_moa.lua:Game.createMonsterType]
- `Game.createMonsterType("Marsh Stalker")` and `mType:register(monster)` [marsh_stalker.lua:Game.createMonsterType]
- `Game.createMonsterType("Parrot")` and `mType:register(monster)` [parrot.lua:Game.createMonsterType]
- `Game.createMonsterType("Penguin")` and `mType:register(monster)` [penguin.lua:Game.createMonsterType]
- `Game.createMonsterType("Pigeon")` and `mType:register(monster)` [pigeon.lua:Game.createMonsterType]
- `Game.createMonsterType("Seagull")` and `mType:register(monster)` [seagull.lua:Game.createMonsterType]
- `Game.createMonsterType("Tame Terror Bird")` and `mType:register(monster)` [tame_terror_bird.lua:Game.createMonsterType]
- `Game.createMonsterType("Terror Bird")` and `mType:register(monster)` [terror_bird.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [agressive_chicken.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [agrestic_chicken.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [agrestic_chicken.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [berserker_chicken.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [berserker_chicken.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [cave_parrot.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cave_parrot.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [chicken.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [chicken.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [demon_parrot.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [demon_parrot.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dire_penguin.lua:monster.Bestiary]

## Side Effects
- Registers monster type `Agressive Chicken` into the global `Game` engine registry via `mType:register(monster)` [agressive_chicken.lua:mType:register]
- Registers monster type `Agrestic Chicken` into the global `Game` engine registry via `mType:register(monster)` [agrestic_chicken.lua:mType:register]
- Registers monster type `Berserker Chicken` into the global `Game` engine registry via `mType:register(monster)` [berserker_chicken.lua:mType:register]
- Registers monster type `Cave Parrot` into the global `Game` engine registry via `mType:register(monster)` [cave_parrot.lua:mType:register]
- Registers monster type `Chicken` into the global `Game` engine registry via `mType:register(monster)` [chicken.lua:mType:register]
- Registers monster type `Demon Parrot` into the global `Game` engine registry via `mType:register(monster)` [demon_parrot.lua:mType:register]
- Registers monster type `Dire Penguin` into the global `Game` engine registry via `mType:register(monster)` [dire_penguin.lua:mType:register]
- Registers monster type `Flamingo` into the global `Game` engine registry via `mType:register(monster)` [flamingo.lua:mType:register]
- Registers monster type `Headpecker` into the global `Game` engine registry via `mType:register(monster)` [headpecker.lua:mType:register]
- Registers monster type `Jungle Moa` into the global `Game` engine registry via `mType:register(monster)` [jungle_moa.lua:mType:register]
- Registers monster type `Marsh Stalker` into the global `Game` engine registry via `mType:register(monster)` [marsh_stalker.lua:mType:register]
- Registers monster type `Parrot` into the global `Game` engine registry via `mType:register(monster)` [parrot.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
