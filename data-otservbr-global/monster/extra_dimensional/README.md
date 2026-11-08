# Extra Dimensional

## Overview
Component package under `monster/extra_dimensional` containing 11 files (`breach_brood.lua`..`yielothax.lua`).

## Interface
- `Game.createMonsterType("Breach Brood")` and `mType:register(monster)` [breach_brood.lua:Game.createMonsterType]
- `Game.createMonsterType("Dread Intruder")` and `mType:register(monster)` [dread_intruder.lua:Game.createMonsterType]
- `Game.createMonsterType("Instable Breach Brood")` and `mType:register(monster)` [instable_breach_brood.lua:Game.createMonsterType]
- `Game.createMonsterType("Instable Sparkion")` and `mType:register(monster)` [instable_sparkion.lua:Game.createMonsterType]
- `Game.createMonsterType("Mitmah Scout")` and `mType:register(monster)` [mitmah_scout.lua:Game.createMonsterType]
- `Game.createMonsterType("Mitmah Seer")` and `mType:register(monster)` [mitmah_seer.lua:Game.createMonsterType]
- `Game.createMonsterType("Reality Reaver")` and `mType:register(monster)` [reality_reaver.lua:Game.createMonsterType]
- `Game.createMonsterType("Sparkion")` and `mType:register(monster)` [sparkion.lua:Game.createMonsterType]
- `Game.createMonsterType("Stabilizing Dread Intruder")` and `mType:register(monster)` [stabilizing_dread_intruder.lua:Game.createMonsterType]
- `Game.createMonsterType("Stabilizing Reality Reaver")` and `mType:register(monster)` [stabilizing_reality_reaver.lua:Game.createMonsterType]
- `Game.createMonsterType("Yielothax")` and `mType:register(monster)` [yielothax.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [breach_brood.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [breach_brood.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dread_intruder.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dread_intruder.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [instable_breach_brood.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [instable_breach_brood.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [instable_sparkion.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [instable_sparkion.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [mitmah_scout.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mitmah_scout.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [mitmah_seer.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mitmah_seer.lua:monster.flags]

## Side Effects
- Registers monster type `Breach Brood` into the global `Game` engine registry via `mType:register(monster)` [breach_brood.lua:mType:register]
- Registers monster type `Dread Intruder` into the global `Game` engine registry via `mType:register(monster)` [dread_intruder.lua:mType:register]
- Registers monster type `Instable Breach Brood` into the global `Game` engine registry via `mType:register(monster)` [instable_breach_brood.lua:mType:register]
- Registers monster type `Instable Sparkion` into the global `Game` engine registry via `mType:register(monster)` [instable_sparkion.lua:mType:register]
- Registers monster type `Mitmah Scout` into the global `Game` engine registry via `mType:register(monster)` [mitmah_scout.lua:mType:register]
- Registers monster type `Mitmah Seer` into the global `Game` engine registry via `mType:register(monster)` [mitmah_seer.lua:mType:register]
- Registers monster type `Reality Reaver` into the global `Game` engine registry via `mType:register(monster)` [reality_reaver.lua:mType:register]
- Registers monster type `Sparkion` into the global `Game` engine registry via `mType:register(monster)` [sparkion.lua:mType:register]
- Registers monster type `Stabilizing Dread Intruder` into the global `Game` engine registry via `mType:register(monster)` [stabilizing_dread_intruder.lua:mType:register]
- Registers monster type `Stabilizing Reality Reaver` into the global `Game` engine registry via `mType:register(monster)` [stabilizing_reality_reaver.lua:mType:register]
- Registers monster type `Yielothax` into the global `Game` engine registry via `mType:register(monster)` [yielothax.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [yielothax.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
