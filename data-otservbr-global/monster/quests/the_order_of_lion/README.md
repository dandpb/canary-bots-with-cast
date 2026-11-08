# The Order Of Lion

## Overview
Provides 2 direct files (`lion_commander.lua`..`usurper_commander.lua`) and 1 subdirectories under `monster/quests/the_order_of_lion`.

## Interface
- `Game.createMonsterType("Lion Commander")` and `mType:register(monster)` [lion_commander.lua:Game.createMonsterType]
- `Game.createMonsterType("Usurper Commander")` and `mType:register(monster)` [usurper_commander.lua:Game.createMonsterType]
- [bosses](./bosses/README.md) - Component package under `monster/quests/the_order_of_lion/bosses` containing 5 files (`ancient_lion_archer.lua`..`kesar.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lion_commander.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [usurper_commander.lua:monster.flags]

## Side Effects
- Registers monster type `Lion Commander` into the global `Game` engine registry via `mType:register(monster)` [lion_commander.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [lion_commander.lua:monster.events]
- Registers monster type `Usurper Commander` into the global `Game` engine registry via `mType:register(monster)` [usurper_commander.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [usurper_commander.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
