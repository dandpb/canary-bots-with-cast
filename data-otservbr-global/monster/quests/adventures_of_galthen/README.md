# Adventures Of Galthen

## Overview
Component package under `monster/quests/adventures_of_galthen` containing 1 files (`megasylvan_yselda.lua`..`megasylvan_yselda.lua`).

## Interface
- `Game.createMonsterType("Megasylvan Yselda")` and `mType:register(monster)` [megasylvan_yselda.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [megasylvan_yselda.lua:monster.flags]

## Side Effects
- Registers monster type `Megasylvan Yselda` into the global `Game` engine registry via `mType:register(monster)` [megasylvan_yselda.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
