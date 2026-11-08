# Bigfoots Burden

## Overview
Provides 4 direct files (`humorless_fungus.lua`..`versperoth.lua`) and 1 subdirectories under `monster/quests/bigfoots_burden`.

## Interface
- `Game.createMonsterType("Humorless Fungus")` and `mType:register(monster)` [humorless_fungus.lua:Game.createMonsterType]
- `Game.createMonsterType("Minion of Versperoth")` and `mType:register(monster)` [minion_of_versperoth.lua:Game.createMonsterType]
- `Game.createMonsterType("Strange Slime")` and `mType:register(monster)` [strange_slime.lua:Game.createMonsterType]
- `Game.createMonsterType("Versperoth")` and `mType:register(monster)` [versperoth.lua:Game.createMonsterType]
- [bosses](./bosses/README.md) - Component package under `monster/quests/bigfoots_burden/bosses` containing 3 files (`abyssador.lua`..`gnomevil.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [humorless_fungus.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [minion_of_versperoth.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [strange_slime.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [versperoth.lua:monster.flags]

## Side Effects
- Registers monster type `Humorless Fungus` into the global `Game` engine registry via `mType:register(monster)` [humorless_fungus.lua:mType:register]
- Registers monster type `Minion of Versperoth` into the global `Game` engine registry via `mType:register(monster)` [minion_of_versperoth.lua:mType:register]
- Registers monster type `Strange Slime` into the global `Game` engine registry via `mType:register(monster)` [strange_slime.lua:mType:register]
- Registers monster type `Versperoth` into the global `Game` engine registry via `mType:register(monster)` [versperoth.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [versperoth.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
