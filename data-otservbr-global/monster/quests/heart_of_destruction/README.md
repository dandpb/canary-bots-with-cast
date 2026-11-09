# Heart Of Destruction

## Overview
Component package under `monster/quests/heart_of_destruction` containing 26 files (`aftershock.lua`..`world_devourer.lua`).

## Interface
- Defines 26 script/configuration files (`aftershock.lua` through `world_devourer.lua`) [aftershock.lua]
- `Game.createMonsterType("Aftershock")` and `mType:register(monster)` [aftershock.lua:Game.createMonsterType]
- `Game.createMonsterType("Anomaly")` and `mType:register(monster)` [anomaly.lua:Game.createMonsterType]
- `Game.createMonsterType("Charged Anomaly")` and `mType:register(monster)` [charged_anomaly.lua:Game.createMonsterType]
- `Game.createMonsterType("Charged Disruption")` and `mType:register(monster)` [charged_disruption.lua:Game.createMonsterType]
- `Game.createMonsterType("Charger")` and `mType:register(monster)` [charger.lua:Game.createMonsterType]
- `Game.createMonsterType("Charging Outburst")` and `mType:register(monster)` [charging_outburst.lua:Game.createMonsterType]
- `Game.createMonsterType("Crackler")` and `mType:register(monster)` [crackler.lua:Game.createMonsterType]
- `Game.createMonsterType("Damage Resonance")` and `mType:register(monster)` [damage_resonance.lua:Game.createMonsterType]
- `Game.createMonsterType("Depolarized Crackler")` and `mType:register(monster)` [depolarized_crackler.lua:Game.createMonsterType]
- `Game.createMonsterType("Disruption")` and `mType:register(monster)` [disruption.lua:Game.createMonsterType]
- `Game.createMonsterType("Eradicator")` and `mType:register(monster)` [eradicator.lua:Game.createMonsterType]
- `Game.createMonsterType("Eradicator2")` and `mType:register(monster)` [eradicator2.lua:Game.createMonsterType]
- `Game.createMonsterType("Foreshock")` and `mType:register(monster)` [foreshock.lua:Game.createMonsterType]
- `Game.createMonsterType("Frenzy")` and `mType:register(monster)` [frenzy.lua:Game.createMonsterType]
- `Game.createMonsterType("Greed")` and `mType:register(monster)` [greed.lua:Game.createMonsterType]
- `Game.createMonsterType("Outburst")` and `mType:register(monster)` [outburst.lua:Game.createMonsterType]
- `Game.createMonsterType("Overcharge")` and `mType:register(monster)` [overcharge.lua:Game.createMonsterType]
- `Game.createMonsterType("Overcharged Disruption")` and `mType:register(monster)` [overcharged_disruption.lua:Game.createMonsterType]
- `Game.createMonsterType("Realityquake")` and `mType:register(monster)` [realityquake.lua:Game.createMonsterType]
- `Game.createMonsterType("Rupture")` and `mType:register(monster)` [rupture.lua:Game.createMonsterType]
- `Game.createMonsterType("Spark of Destruction")` and `mType:register(monster)` [spark_of_destruction.lua:Game.createMonsterType]
- `Game.createMonsterType("The Destruction")` and `mType:register(monster)` [the_destruction.lua:Game.createMonsterType]
- `Game.createMonsterType("The Hunger")` and `mType:register(monster)` [the_hunger.lua:Game.createMonsterType]
- `Game.createMonsterType("The Rage")` and `mType:register(monster)` [the_rage.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [aftershock.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [anomaly.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [charged_anomaly.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [charged_disruption.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [charger.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [charging_outburst.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [crackler.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [damage_resonance.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [depolarized_crackler.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [disruption.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [eradicator.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [eradicator2.lua:monster.flags]

## Side Effects
- Registers monster type `Aftershock` into the global `Game` engine registry via `mType:register(monster)` [aftershock.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [aftershock.lua:monster.events]
- Registers monster type `Anomaly` into the global `Game` engine registry via `mType:register(monster)` [anomaly.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [anomaly.lua:monster.events]
- Registers monster type `Charged Anomaly` into the global `Game` engine registry via `mType:register(monster)` [charged_anomaly.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [charged_anomaly.lua:monster.events]
- Registers monster type `Charged Disruption` into the global `Game` engine registry via `mType:register(monster)` [charged_disruption.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [charged_disruption.lua:monster.events]
- Registers monster type `Charger` into the global `Game` engine registry via `mType:register(monster)` [charger.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [charger.lua:monster.events]
- Registers monster type `Charging Outburst` into the global `Game` engine registry via `mType:register(monster)` [charging_outburst.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [charging_outburst.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
