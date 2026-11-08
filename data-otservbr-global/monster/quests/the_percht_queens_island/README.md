# The Percht Queens Island

## Overview
Component package under `monster/quests/the_percht_queens_island` containing 10 files (`baleful_bunny.lua`..`warm_fire.lua`).

## Interface
- `Game.createMonsterType("Baleful Bunny")` and `mType:register(monster)` [baleful_bunny.lua:Game.createMonsterType]
- `Game.createMonsterType("Bonny Bunny")` and `mType:register(monster)` [bonny_bunny.lua:Game.createMonsterType]
- `Game.createMonsterType("Bright Percht Sleigh")` and `mType:register(monster)` [bright_percht_sleigh.lua:Game.createMonsterType]
- `Game.createMonsterType("Cold Percht Sleigh")` and `mType:register(monster)` [cold_percht_sleigh.lua:Game.createMonsterType]
- `Game.createMonsterType("Dark Percht Sleigh")` and `mType:register(monster)` [dark_percht_sleigh.lua:Game.createMonsterType]
- `Game.createMonsterType("Percht")` and `mType:register(monster)` [percht.lua:Game.createMonsterType]
- `Game.createMonsterType("Percht Minion")` and `mType:register(monster)` [percht_minion.lua:Game.createMonsterType]
- `Game.createMonsterType("Schiach")` and `mType:register(monster)` [schiach.lua:Game.createMonsterType]
- `Game.createMonsterType("The Percht Queen")` and `mType:register(monster)` [the_percht_queen.lua:Game.createMonsterType]
- `Game.createMonsterType("Warm Fire")` and `mType:register(monster)` [warm_fire.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [baleful_bunny.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [baleful_bunny.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bonny_bunny.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bright_percht_sleigh.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cold_percht_sleigh.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dark_percht_sleigh.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [percht.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [percht.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [percht_minion.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [schiach.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [schiach.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_percht_queen.lua:monster.flags]

## Side Effects
- Registers monster type `Baleful Bunny` into the global `Game` engine registry via `mType:register(monster)` [baleful_bunny.lua:mType:register]
- Registers monster type `Bonny Bunny` into the global `Game` engine registry via `mType:register(monster)` [bonny_bunny.lua:mType:register]
- Registers monster type `Bright Percht Sleigh` into the global `Game` engine registry via `mType:register(monster)` [bright_percht_sleigh.lua:mType:register]
- Registers monster type `Cold Percht Sleigh` into the global `Game` engine registry via `mType:register(monster)` [cold_percht_sleigh.lua:mType:register]
- Registers monster type `Dark Percht Sleigh` into the global `Game` engine registry via `mType:register(monster)` [dark_percht_sleigh.lua:mType:register]
- Registers monster type `Percht` into the global `Game` engine registry via `mType:register(monster)` [percht.lua:mType:register]
- Registers monster type `Percht Minion` into the global `Game` engine registry via `mType:register(monster)` [percht_minion.lua:mType:register]
- Registers monster type `Schiach` into the global `Game` engine registry via `mType:register(monster)` [schiach.lua:mType:register]
- Registers monster type `The Percht Queen` into the global `Game` engine registry via `mType:register(monster)` [the_percht_queen.lua:mType:register]
- Registers monster type `Warm Fire` into the global `Game` engine registry via `mType:register(monster)` [warm_fire.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
