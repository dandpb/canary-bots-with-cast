# Raids

## Overview
Component package under `monster/raids` containing 55 files (`arachir_the_ancient_one.lua`..`zulazza_the_corruptor.lua`).

## Interface
- Defines 55 script/configuration files (`arachir_the_ancient_one.lua` through `zulazza_the_corruptor.lua`) [arachir_the_ancient_one.lua]
- `Game.createMonsterType("Arachir the Ancient One")` and `mType:register(monster)` [arachir_the_ancient_one.lua:Game.createMonsterType]
- `Game.createMonsterType("Barbaria")` and `mType:register(monster)` [barbaria.lua:Game.createMonsterType]
- `Game.createMonsterType("Battlemaster Zunzu")` and `mType:register(monster)` [battlemaster_zunzu.lua:Game.createMonsterType]
- `Game.createMonsterType("Brutus Bloodbeard")` and `mType:register(monster)` [brutus_bloodbeard.lua:Game.createMonsterType]
- `Game.createMonsterType("Captain Jones")` and `mType:register(monster)` [captain_jones.lua:Game.createMonsterType]
- `Game.createMonsterType("Chayenne")` and `mType:register(monster)` [chayenne.lua:Game.createMonsterType]
- `Game.createMonsterType("Chizzoron the Distorter")` and `mType:register(monster)` [chizzoron_the_distorter.lua:Game.createMonsterType]
- `Game.createMonsterType("Control Tower")` and `mType:register(monster)` [control_tower.lua:Game.createMonsterType]
- `Game.createMonsterType("Deadeye Devious")` and `mType:register(monster)` [deadeye_devious.lua:Game.createMonsterType]
- `Game.createMonsterType("Draptor")` and `mType:register(monster)` [draptor.lua:Game.createMonsterType]
- `Game.createMonsterType("Egg")` and `mType:register(monster)` [egg_the_welter.lua:Game.createMonsterType]
- `Game.createMonsterType("Fernfang")` and `mType:register(monster)` [fernfang.lua:Game.createMonsterType]
- `Game.createMonsterType("Ferumbras")` and `mType:register(monster)` [ferumbras.lua:Game.createMonsterType]
- `Game.createMonsterType("Fleabringer")` and `mType:register(monster)` [fleabringer.lua:Game.createMonsterType]
- `Game.createMonsterType("Foreman Kneebiter")` and `mType:register(monster)` [foreman_kneebiter.lua:Game.createMonsterType]
- `Game.createMonsterType("Frost Servant")` and `mType:register(monster)` [frost_servant.lua:Game.createMonsterType]
- `Game.createMonsterType("Furyosa")` and `mType:register(monster)` [furyosa.lua:Game.createMonsterType]
- `Game.createMonsterType("Ghazbaran")` and `mType:register(monster)` [ghazbaran.lua:Game.createMonsterType]
- `Game.createMonsterType("Giant Spider Wyda")` and `mType:register(monster)` [giant_spider_wyda.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth Battery")` and `mType:register(monster)` [glooth_battery.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth Bomb")` and `mType:register(monster)` [glooth_bomb.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth Fairy")` and `mType:register(monster)` [glooth_fairy.lua:Game.createMonsterType]
- `Game.createMonsterType("Grand Mother Foulscale")` and `mType:register(monster)` [grand_mother_foulscale.lua:Game.createMonsterType]
- `Game.createMonsterType("Grorlam")` and `mType:register(monster)` [grorlam.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [arachir_the_ancient_one.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [barbaria.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [battlemaster_zunzu.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brutus_bloodbeard.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [captain_jones.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [chayenne.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [chizzoron_the_distorter.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [control_tower.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [deadeye_devious.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [draptor.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [draptor.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [egg_the_welter.lua:monster.flags]

## Side Effects
- Registers monster type `Arachir the Ancient One` into the global `Game` engine registry via `mType:register(monster)` [arachir_the_ancient_one.lua:mType:register]
- Registers monster type `Barbaria` into the global `Game` engine registry via `mType:register(monster)` [barbaria.lua:mType:register]
- Registers monster type `Battlemaster Zunzu` into the global `Game` engine registry via `mType:register(monster)` [battlemaster_zunzu.lua:mType:register]
- Registers monster type `Brutus Bloodbeard` into the global `Game` engine registry via `mType:register(monster)` [brutus_bloodbeard.lua:mType:register]
- Registers monster type `Captain Jones` into the global `Game` engine registry via `mType:register(monster)` [captain_jones.lua:mType:register]
- Registers monster type `Chayenne` into the global `Game` engine registry via `mType:register(monster)` [chayenne.lua:mType:register]
- Registers monster type `Chizzoron the Distorter` into the global `Game` engine registry via `mType:register(monster)` [chizzoron_the_distorter.lua:mType:register]
- Registers monster type `Control Tower` into the global `Game` engine registry via `mType:register(monster)` [control_tower.lua:mType:register]
- Registers monster type `Deadeye Devious` into the global `Game` engine registry via `mType:register(monster)` [deadeye_devious.lua:mType:register]
- Registers monster type `Draptor` into the global `Game` engine registry via `mType:register(monster)` [draptor.lua:mType:register]
- Registers monster type `Egg` into the global `Game` engine registry via `mType:register(monster)` [egg_the_welter.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [egg_the_welter.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
