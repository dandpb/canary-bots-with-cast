# Dangerous Depth

## Overview
Provides 12 direct files (`aggressive_lava.lua`..`snail_slime.lua`) and 1 subdirectories under `monster/quests/dangerous_depth`.

## Interface
- `Game.createMonsterType("Aggressive Lava")` and `mType:register(monster)` [aggressive_lava.lua:Game.createMonsterType]
- `Game.createMonsterType("Aggressive Matter")` and `mType:register(monster)` [aggressive_matter.lua:Game.createMonsterType]
- `Game.createMonsterType("Captured Dwarf")` and `mType:register(monster)` [captured_dwarf.lua:Game.createMonsterType]
- `Game.createMonsterType("Ember Beast")` and `mType:register(monster)` [ember_beast.lua:Game.createMonsterType]
- `Game.createMonsterType("Fiery Blood")` and `mType:register(monster)` [fiery_blood.lua:Game.createMonsterType]
- `Game.createMonsterType("Fiery Heart")` and `mType:register(monster)` [fiery_heart.lua:Game.createMonsterType]
- `Game.createMonsterType("Gnome Pack Crawler")` and `mType:register(monster)` [gnome_pack_crawler.lua:Game.createMonsterType]
- `Game.createMonsterType("Lava Lurker Attendant")` and `mType:register(monster)` [lava_lurker_attendant.lua:Game.createMonsterType]
- `Game.createMonsterType("Lost Gnome")` and `mType:register(monster)` [lost_gnome.lua:Game.createMonsterType]
- `Game.createMonsterType("Makeshift Home")` and `mType:register(monster)` [makeshift_home.lua:Game.createMonsterType]
- `Game.createMonsterType("Organic Matter")` and `mType:register(monster)` [organic_matter.lua:Game.createMonsterType]
- `Game.createMonsterType("Snail Slime")` and `mType:register(monster)` [snail_slime.lua:Game.createMonsterType]
- [bosses](./bosses/README.md) - Component package under `monster/quests/dangerous_depth/bosses` containing 6 files (`ancient_spawn_of_morgathla.lua`..`the_hungry_baron_from_below.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [aggressive_lava.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [aggressive_matter.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [captured_dwarf.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ember_beast.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fiery_blood.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fiery_heart.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [gnome_pack_crawler.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lava_lurker_attendant.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lost_gnome.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [makeshift_home.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [organic_matter.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [snail_slime.lua:monster.flags]

## Side Effects
- Registers monster type `Aggressive Lava` into the global `Game` engine registry via `mType:register(monster)` [aggressive_lava.lua:mType:register]
- Registers monster type `Aggressive Matter` into the global `Game` engine registry via `mType:register(monster)` [aggressive_matter.lua:mType:register]
- Registers monster type `Captured Dwarf` into the global `Game` engine registry via `mType:register(monster)` [captured_dwarf.lua:mType:register]
- Registers monster type `Ember Beast` into the global `Game` engine registry via `mType:register(monster)` [ember_beast.lua:mType:register]
- Registers monster type `Fiery Blood` into the global `Game` engine registry via `mType:register(monster)` [fiery_blood.lua:mType:register]
- Registers monster type `Fiery Heart` into the global `Game` engine registry via `mType:register(monster)` [fiery_heart.lua:mType:register]
- Registers monster type `Gnome Pack Crawler` into the global `Game` engine registry via `mType:register(monster)` [gnome_pack_crawler.lua:mType:register]
- Registers monster type `Lava Lurker Attendant` into the global `Game` engine registry via `mType:register(monster)` [lava_lurker_attendant.lua:mType:register]
- Registers monster type `Lost Gnome` into the global `Game` engine registry via `mType:register(monster)` [lost_gnome.lua:mType:register]
- Registers monster type `Makeshift Home` into the global `Game` engine registry via `mType:register(monster)` [makeshift_home.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [makeshift_home.lua:monster.events]
- Registers monster type `Organic Matter` into the global `Game` engine registry via `mType:register(monster)` [organic_matter.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
