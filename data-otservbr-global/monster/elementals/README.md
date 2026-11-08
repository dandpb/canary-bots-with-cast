# Elementals

## Overview
Component package under `monster/elementals` containing 19 files (`candy_floss_elemental.lua`..`water_elemental.lua`).

## Interface
- `Game.createMonsterType("Candy Floss Elemental")` and `mType:register(monster)` [candy_floss_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Cliff Strider")` and `mType:register(monster)` [cliff_strider.lua:Game.createMonsterType]
- `Game.createMonsterType("Earth Elemental")` and `mType:register(monster)` [earth_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Energy Elemental")` and `mType:register(monster)` [energy_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Fire Elemental")` and `mType:register(monster)` [fire_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Foam Stalker")` and `mType:register(monster)` [foam_stalker.lua:Game.createMonsterType]
- `Game.createMonsterType("High Voltage Elemental")` and `mType:register(monster)` [high_voltage_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Honey Elemental")` and `mType:register(monster)` [honey_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Ironblight")` and `mType:register(monster)` [ironblight.lua:Game.createMonsterType]
- `Game.createMonsterType("Knowledge Elemental")` and `mType:register(monster)` [knowledge_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Lava Lurker")` and `mType:register(monster)` [lava_lurker.lua:Game.createMonsterType]
- `Game.createMonsterType("Massive Earth Elemental")` and `mType:register(monster)` [massive_earth_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Massive Energy Elemental")` and `mType:register(monster)` [massive_energy_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Massive Fire Elemental")` and `mType:register(monster)` [massive_fire_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Massive Water Elemental")` and `mType:register(monster)` [massive_water_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Raging Fire")` and `mType:register(monster)` [raging_fire.lua:Game.createMonsterType]
- `Game.createMonsterType("Ravenous Lava Lurker")` and `mType:register(monster)` [ravenous_lava_lurker.lua:Game.createMonsterType]
- `Game.createMonsterType("Sulphur Spouter")` and `mType:register(monster)` [sulphur_spouter.lua:Game.createMonsterType]
- `Game.createMonsterType("Water Elemental")` and `mType:register(monster)` [water_elemental.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [candy_floss_elemental.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [candy_floss_elemental.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [cliff_strider.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cliff_strider.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [earth_elemental.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [earth_elemental.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [energy_elemental.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [energy_elemental.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [fire_elemental.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fire_elemental.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [foam_stalker.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [foam_stalker.lua:monster.flags]

## Side Effects
- Registers monster type `Candy Floss Elemental` into the global `Game` engine registry via `mType:register(monster)` [candy_floss_elemental.lua:mType:register]
- Registers monster type `Cliff Strider` into the global `Game` engine registry via `mType:register(monster)` [cliff_strider.lua:mType:register]
- Registers monster type `Earth Elemental` into the global `Game` engine registry via `mType:register(monster)` [earth_elemental.lua:mType:register]
- Registers monster type `Energy Elemental` into the global `Game` engine registry via `mType:register(monster)` [energy_elemental.lua:mType:register]
- Registers monster type `Fire Elemental` into the global `Game` engine registry via `mType:register(monster)` [fire_elemental.lua:mType:register]
- Registers monster type `Foam Stalker` into the global `Game` engine registry via `mType:register(monster)` [foam_stalker.lua:mType:register]
- Registers monster type `High Voltage Elemental` into the global `Game` engine registry via `mType:register(monster)` [high_voltage_elemental.lua:mType:register]
- Registers monster type `Honey Elemental` into the global `Game` engine registry via `mType:register(monster)` [honey_elemental.lua:mType:register]
- Registers monster type `Ironblight` into the global `Game` engine registry via `mType:register(monster)` [ironblight.lua:mType:register]
- Registers monster type `Knowledge Elemental` into the global `Game` engine registry via `mType:register(monster)` [knowledge_elemental.lua:mType:register]
- Registers monster type `Lava Lurker` into the global `Game` engine registry via `mType:register(monster)` [lava_lurker.lua:mType:register]
- Registers monster type `Massive Earth Elemental` into the global `Game` engine registry via `mType:register(monster)` [massive_earth_elemental.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
