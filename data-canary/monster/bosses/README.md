# Boss Monsters (`data-canary/monster/bosses`)

## Overview
Defines and registers 8 reward boss `MonsterType` definitions (`rewardBoss = true`) for the `data-canary` datapack.

## Interface
- `[apocalypse.lua:mType]` — `Game.createMonsterType("Apocalypse")` (`health = 160000`, `experience = 550000`, `rewardBoss = true`), registered via `mType:register(monster)`.
- `[apprentice_sheng.lua:mType]` — `Game.createMonsterType("Apprentice Sheng")` (`health = 95`, `experience = 150`, `rewardBoss = true`), registered via `mType:register(monster)`.
- `[bazir.lua:mType]` — `Game.createMonsterType("Bazir")` (`health = 110000`, `experience = 300000`, `rewardBoss = true`), registered via `mType:register(monster)`.
- `[black_knight.lua:mType]` — `Game.createMonsterType("Black Knight")` (`health = 1800`, `experience = 1600`, `rewardBoss = true`), registered via `mType:register(monster)`.
- `[bullwark.lua:mType]` — `Game.createMonsterType("Bullwark")` (`health = 65000`, `experience = 16725`, `rewardBoss = true`), registered via `mType:register(monster)`.
- `[custodian.lua:mType]` — `Game.createMonsterType("Custodian")` (`health = 47000`, `experience = 27500`, `rewardBoss = true`), registered via `mType:register(monster)`.
- `[dharalion.lua:mType]` — `Game.createMonsterType("Dharalion")` (`health = 380`, `experience = 380`, `rewardBoss = true`), registered via `mType:register(monster)`.
- `[shadowpelt.lua:mType]` — `Game.createMonsterType("Shadowpelt")` (`health = 5000`, `experience = 4000`, `rewardBoss = true`), registered via `mType:register(monster)`.

## Invariants
- All 8 boss definitions set `monster.flags.rewardBoss = true`, `summonable = false`, and `convinceable = false`.

## Side Effects
- Each file invokes `Game.createMonsterType(...)` and `mType:register(monster)` to register its boss `MonsterType` in the global game engine registry at startup/reload.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
