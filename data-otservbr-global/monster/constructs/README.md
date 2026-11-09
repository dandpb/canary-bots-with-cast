# Constructs

## Overview
Component package under `monster/constructs` containing 31 files (`animated_snowman.lua`..`worker_golem.lua`).

## Interface
- Defines 31 script/configuration files (`animated_snowman.lua` through `worker_golem.lua`) [animated_snowman.lua]
- `Game.createMonsterType("Animated Snowman")` and `mType:register(monster)` [animated_snowman.lua:Game.createMonsterType]
- `Game.createMonsterType("Biting Book")` and `mType:register(monster)` [biting_book.lua:Game.createMonsterType]
- `Game.createMonsterType("Clay Guardian")` and `mType:register(monster)` [clay_guardian.lua:Game.createMonsterType]
- `Game.createMonsterType("Damaged Crystal Golem")` and `mType:register(monster)` [damaged_crystal_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Damaged Worker Golem")` and `mType:register(monster)` [damaged_worker_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Diamond Servant")` and `mType:register(monster)` [diamond_servant.lua:Game.createMonsterType]
- `Game.createMonsterType("Diamond Servant Replica")` and `mType:register(monster)` [diamond_servant_replica.lua:Game.createMonsterType]
- `Game.createMonsterType("Enraged Crystal Golem")` and `mType:register(monster)` [enraged_crystal_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Eternal Guardian")` and `mType:register(monster)` [eternal_guardian.lua:Game.createMonsterType]
- `Game.createMonsterType("Gingerbread Man")` and `mType:register(monster)` [gingerbread_men.lua:Game.createMonsterType]
- `Game.createMonsterType("Glooth Golem")` and `mType:register(monster)` [glooth_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Goggle Cake")` and `mType:register(monster)` [goggle_cake.lua:Game.createMonsterType]
- `Game.createMonsterType("Golden Servant")` and `mType:register(monster)` [golden_servant.lua:Game.createMonsterType]
- `Game.createMonsterType("Golden Servant Replica")` and `mType:register(monster)` [golden_servant_replica.lua:Game.createMonsterType]
- `Game.createMonsterType("Ice Golem")` and `mType:register(monster)` [ice_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Infected Weeper")` and `mType:register(monster)` [infected_weeper.lua:Game.createMonsterType]
- `Game.createMonsterType("Iron Servant")` and `mType:register(monster)` [iron_servant.lua:Game.createMonsterType]
- `Game.createMonsterType("Iron Servant Replica")` and `mType:register(monster)` [iron_servant_replica.lua:Game.createMonsterType]
- `Game.createMonsterType("Lava Golem")` and `mType:register(monster)` [lava_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Magma Crawler")` and `mType:register(monster)` [magma_crawler.lua:Game.createMonsterType]
- `Game.createMonsterType("Metal Gargoyle")` and `mType:register(monster)` [metal_gargoyle.lua:Game.createMonsterType]
- `Game.createMonsterType("Orewalker")` and `mType:register(monster)` [orewalker.lua:Game.createMonsterType]
- `Game.createMonsterType("Rustheap Golem")` and `mType:register(monster)` [rustheap_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Sandstone Scorpion")` and `mType:register(monster)` [sandstone_scorpion.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [animated_snowman.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_snowman.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [biting_book.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [biting_book.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [clay_guardian.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [clay_guardian.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [damaged_crystal_golem.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [damaged_crystal_golem.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [damaged_worker_golem.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [damaged_worker_golem.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [diamond_servant.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [diamond_servant.lua:monster.flags]

## Side Effects
- Registers monster type `Animated Snowman` into the global `Game` engine registry via `mType:register(monster)` [animated_snowman.lua:mType:register]
- Registers monster type `Biting Book` into the global `Game` engine registry via `mType:register(monster)` [biting_book.lua:mType:register]
- Registers monster type `Clay Guardian` into the global `Game` engine registry via `mType:register(monster)` [clay_guardian.lua:mType:register]
- Registers monster type `Damaged Crystal Golem` into the global `Game` engine registry via `mType:register(monster)` [damaged_crystal_golem.lua:mType:register]
- Registers monster type `Damaged Worker Golem` into the global `Game` engine registry via `mType:register(monster)` [damaged_worker_golem.lua:mType:register]
- Registers monster type `Diamond Servant` into the global `Game` engine registry via `mType:register(monster)` [diamond_servant.lua:mType:register]
- Registers monster type `Diamond Servant Replica` into the global `Game` engine registry via `mType:register(monster)` [diamond_servant_replica.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [diamond_servant_replica.lua:monster.events]
- Registers monster type `Enraged Crystal Golem` into the global `Game` engine registry via `mType:register(monster)` [enraged_crystal_golem.lua:mType:register]
- Registers monster type `Eternal Guardian` into the global `Game` engine registry via `mType:register(monster)` [eternal_guardian.lua:mType:register]
- Registers monster type `Gingerbread Man` into the global `Game` engine registry via `mType:register(monster)` [gingerbread_men.lua:mType:register]
- Registers monster type `Glooth Golem` into the global `Game` engine registry via `mType:register(monster)` [glooth_golem.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
