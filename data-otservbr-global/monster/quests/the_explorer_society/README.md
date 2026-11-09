# The Explorer Society

## Overview
Component package under `monster/quests/the_explorer_society` containing 5 files (`blue_butterfly.lua`..`yellow_butterfly.lua`).

## Interface
- `Game.createMonsterType("Blue Butterfly")` and `mType:register(monster)` [blue_butterfly.lua:Game.createMonsterType]
- `Game.createMonsterType("Pink Butterfly")` and `mType:register(monster)` [pink_butterfly.lua:Game.createMonsterType]
- `Game.createMonsterType("Purple Butterfly")` and `mType:register(monster)` [purple_butterfly.lua:Game.createMonsterType]
- `Game.createMonsterType("Red Butterfly")` and `mType:register(monster)` [red_butterfly.lua:Game.createMonsterType]
- `Game.createMonsterType("Yellow Butterfly")` and `mType:register(monster)` [yellow_butterfly.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [blue_butterfly.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [blue_butterfly.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [pink_butterfly.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [pink_butterfly.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [purple_butterfly.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [purple_butterfly.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [red_butterfly.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [red_butterfly.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [yellow_butterfly.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [yellow_butterfly.lua:monster.flags]

## Side Effects
- Registers monster type `Blue Butterfly` into the global `Game` engine registry via `mType:register(monster)` [blue_butterfly.lua:mType:register]
- Registers monster type `Pink Butterfly` into the global `Game` engine registry via `mType:register(monster)` [pink_butterfly.lua:mType:register]
- Registers monster type `Purple Butterfly` into the global `Game` engine registry via `mType:register(monster)` [purple_butterfly.lua:mType:register]
- Registers monster type `Red Butterfly` into the global `Game` engine registry via `mType:register(monster)` [red_butterfly.lua:mType:register]
- Registers monster type `Yellow Butterfly` into the global `Game` engine registry via `mType:register(monster)` [yellow_butterfly.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
