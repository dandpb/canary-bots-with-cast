# Liquid Black

## Overview
Component package under `monster/quests/liquid_black` containing 3 files (`jaul.lua`..`tanjis.lua`).

## Interface
- `Game.createMonsterType("Jaul")` and `mType:register(monster)` [jaul.lua:Game.createMonsterType]
- `Game.createMonsterType("Obujos")` and `mType:register(monster)` [obujos.lua:Game.createMonsterType]
- `Game.createMonsterType("Tanjis")` and `mType:register(monster)` [tanjis.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [jaul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [obujos.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [tanjis.lua:monster.flags]

## Side Effects
- Registers monster type `Jaul` into the global `Game` engine registry via `mType:register(monster)` [jaul.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [jaul.lua:monster.events]
- Registers monster type `Obujos` into the global `Game` engine registry via `mType:register(monster)` [obujos.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [obujos.lua:monster.events]
- Registers monster type `Tanjis` into the global `Game` engine registry via `mType:register(monster)` [tanjis.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [tanjis.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
