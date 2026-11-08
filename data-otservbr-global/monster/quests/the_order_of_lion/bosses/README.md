# Bosses

## Overview
Component package under `monster/quests/the_order_of_lion/bosses` containing 5 files (`ancient_lion_archer.lua`..`kesar.lua`).

## Interface
- `Game.createMonsterType("Ancient Lion Archer")` and `mType:register(monster)` [ancient_lion_archer.lua:Game.createMonsterType]
- `Game.createMonsterType("Ancient Lion Knight")` and `mType:register(monster)` [ancient_lion_knight.lua:Game.createMonsterType]
- `Game.createMonsterType("Ancient Lion Warlock")` and `mType:register(monster)` [ancient_lion_warlock.lua:Game.createMonsterType]
- `Game.createMonsterType("Drume")` and `mType:register(monster)` [drume.lua:Game.createMonsterType]
- `Game.createMonsterType("Kesar")` and `mType:register(monster)` [kesar.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ancient_lion_archer.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ancient_lion_knight.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ancient_lion_warlock.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [drume.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [kesar.lua:monster.flags]

## Side Effects
- Registers monster type `Ancient Lion Archer` into the global `Game` engine registry via `mType:register(monster)` [ancient_lion_archer.lua:mType:register]
- Registers monster type `Ancient Lion Knight` into the global `Game` engine registry via `mType:register(monster)` [ancient_lion_knight.lua:mType:register]
- Registers monster type `Ancient Lion Warlock` into the global `Game` engine registry via `mType:register(monster)` [ancient_lion_warlock.lua:mType:register]
- Registers monster type `Drume` into the global `Game` engine registry via `mType:register(monster)` [drume.lua:mType:register]
- Registers monster type `Kesar` into the global `Game` engine registry via `mType:register(monster)` [kesar.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [kesar.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
