# Bosses

## Overview
Component package under `monster/quests/forgotten_knowledge/bosses` containing 14 files (`dragonking_zyrtarch.lua`..`thorn_steed.lua`).

## Interface
- `Game.createMonsterType("Dragonking Zyrtarch")` and `mType:register(monster)` [dragonking_zyrtarch.lua:Game.createMonsterType]
- `Game.createMonsterType("Lady Tenebris")` and `mType:register(monster)` [lady_tenebris.lua:Game.createMonsterType]
- `Game.createMonsterType("Lloyd")` and `mType:register(monster)` [lloyd.lua:Game.createMonsterType]
- `Game.createMonsterType("Melting Frozen Horror")` and `mType:register(monster)` [melting_frozen_horror.lua:Game.createMonsterType]
- `Game.createMonsterType("Mounted Thorn Knight")` and `mType:register(monster)` [mounted_thorn_knight.lua:Game.createMonsterType]
- `Game.createMonsterType("Solid Frozen Horror")` and `mType:register(monster)` [solid_frozen_horror.lua:Game.createMonsterType]
- `Game.createMonsterType("Soul of Dragonking Zyrtarch")` and `mType:register(monster)` [soul_of_dragonking_zyrtarch.lua:Game.createMonsterType]
- `Game.createMonsterType("The Blazing Time Guardian")` and `mType:register(monster)` [the_blazing_time_guardian.lua:Game.createMonsterType]
- `Game.createMonsterType("The Enraged Thorn Knight")` and `mType:register(monster)` [the_enraged_thorn_knight.lua:Game.createMonsterType]
- `Game.createMonsterType("The Freezing Time Guardian")` and `mType:register(monster)` [the_freezing_time_guardian.lua:Game.createMonsterType]
- `Game.createMonsterType("The Last Lore Keeper")` and `mType:register(monster)` [the_last_lore_keeper.lua:Game.createMonsterType]
- `Game.createMonsterType("The Shielded Thorn Knight")` and `mType:register(monster)` [the_shielded_thorn_knight.lua:Game.createMonsterType]
- `Game.createMonsterType("The Time Guardian")` and `mType:register(monster)` [the_time_guardian.lua:Game.createMonsterType]
- `Game.createMonsterType("Thorn Steed")` and `mType:register(monster)` [thorn_steed.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dragonking_zyrtarch.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lady_tenebris.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lloyd.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [melting_frozen_horror.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mounted_thorn_knight.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [solid_frozen_horror.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [soul_of_dragonking_zyrtarch.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_blazing_time_guardian.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_enraged_thorn_knight.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_freezing_time_guardian.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_last_lore_keeper.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_shielded_thorn_knight.lua:monster.flags]

## Side Effects
- Registers monster type `Dragonking Zyrtarch` into the global `Game` engine registry via `mType:register(monster)` [dragonking_zyrtarch.lua:mType:register]
- Registers monster type `Lady Tenebris` into the global `Game` engine registry via `mType:register(monster)` [lady_tenebris.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [lady_tenebris.lua:monster.events]
- Registers monster type `Lloyd` into the global `Game` engine registry via `mType:register(monster)` [lloyd.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [lloyd.lua:monster.events]
- Registers monster type `Melting Frozen Horror` into the global `Game` engine registry via `mType:register(monster)` [melting_frozen_horror.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [melting_frozen_horror.lua:monster.events]
- Registers monster type `Mounted Thorn Knight` into the global `Game` engine registry via `mType:register(monster)` [mounted_thorn_knight.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [mounted_thorn_knight.lua:monster.events]
- Registers monster type `Solid Frozen Horror` into the global `Game` engine registry via `mType:register(monster)` [solid_frozen_horror.lua:mType:register]
- Registers monster type `Soul of Dragonking Zyrtarch` into the global `Game` engine registry via `mType:register(monster)` [soul_of_dragonking_zyrtarch.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [soul_of_dragonking_zyrtarch.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
