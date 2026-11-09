# Ancient Tombs

## Overview
Component package under `monster/quests/ancient_tombs` containing 10 files (`ashmunrah.lua`..`vashresamun.lua`).

## Interface
- `Game.createMonsterType("Ashmunrah")` and `mType:register(monster)` [ashmunrah.lua:Game.createMonsterType]
- `Game.createMonsterType("Dipthrah")` and `mType:register(monster)` [dipthrah.lua:Game.createMonsterType]
- `Game.createMonsterType("Horestis")` and `mType:register(monster)` [horestis.lua:Game.createMonsterType]
- `Game.createMonsterType("Mahrdis")` and `mType:register(monster)` [mahrdis.lua:Game.createMonsterType]
- `Game.createMonsterType("Morguthis")` and `mType:register(monster)` [morguthis.lua:Game.createMonsterType]
- `Game.createMonsterType("Omruc")` and `mType:register(monster)` [omruc.lua:Game.createMonsterType]
- `Game.createMonsterType("Rahemos")` and `mType:register(monster)` [rahemos.lua:Game.createMonsterType]
- `Game.createMonsterType("Shredderthrower")` and `mType:register(monster)` [shredderthrower.lua:Game.createMonsterType]
- `Game.createMonsterType("Thalas")` and `mType:register(monster)` [thalas.lua:Game.createMonsterType]
- `Game.createMonsterType("Vashresamun")` and `mType:register(monster)` [vashresamun.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ashmunrah.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dipthrah.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [horestis.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mahrdis.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [morguthis.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [omruc.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rahemos.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [shredderthrower.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [thalas.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [vashresamun.lua:monster.flags]

## Side Effects
- Registers monster type `Ashmunrah` into the global `Game` engine registry via `mType:register(monster)` [ashmunrah.lua:mType:register]
- Registers monster type `Dipthrah` into the global `Game` engine registry via `mType:register(monster)` [dipthrah.lua:mType:register]
- Registers monster type `Horestis` into the global `Game` engine registry via `mType:register(monster)` [horestis.lua:mType:register]
- Registers monster type `Mahrdis` into the global `Game` engine registry via `mType:register(monster)` [mahrdis.lua:mType:register]
- Registers monster type `Morguthis` into the global `Game` engine registry via `mType:register(monster)` [morguthis.lua:mType:register]
- Registers monster type `Omruc` into the global `Game` engine registry via `mType:register(monster)` [omruc.lua:mType:register]
- Registers monster type `Rahemos` into the global `Game` engine registry via `mType:register(monster)` [rahemos.lua:mType:register]
- Registers monster type `Shredderthrower` into the global `Game` engine registry via `mType:register(monster)` [shredderthrower.lua:mType:register]
- Registers monster type `Thalas` into the global `Game` engine registry via `mType:register(monster)` [thalas.lua:mType:register]
- Registers monster type `Vashresamun` into the global `Game` engine registry via `mType:register(monster)` [vashresamun.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
