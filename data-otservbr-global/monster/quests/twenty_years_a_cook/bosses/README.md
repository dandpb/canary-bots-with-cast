# Bosses

## Overview
Component package under `monster/quests/twenty_years_a_cook/bosses` containing 1 files (`dragon_hoard.lua`..`dragon_hoard.lua`).

## Interface
- `Game.createMonsterType("Dragon Hoard")` and `mType:register(monster)` [dragon_hoard.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [dragon_hoard.lua:mType.onThink]
- `mType.onAppear` lifecycle callback [dragon_hoard.lua:mType.onAppear]
- `mType.onDisappear` lifecycle callback [dragon_hoard.lua:mType.onDisappear]
- `mType.onMove` lifecycle callback [dragon_hoard.lua:mType.onMove]
- `mType.onSay` lifecycle callback [dragon_hoard.lua:mType.onSay]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragon_hoard.lua:monster.flags]

## Side Effects
- Registers monster type `Dragon Hoard` into the global `Game` engine registry via `mType:register(monster)` [dragon_hoard.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [dragon_hoard.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
