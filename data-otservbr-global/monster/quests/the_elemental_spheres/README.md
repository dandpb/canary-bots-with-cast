# The Elemental Spheres

## Overview
Component package under `monster/quests/the_elemental_spheres` containing 16 files (`blazing_fire_elemental.lua`..`spirit_overlord.lua`).

## Interface
- `Game.createMonsterType("Blazing Fire Elemental")` and `mType:register(monster)` [blazing_fire_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Blistering Fire Elemental")` and `mType:register(monster)` [blistering_fire_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Charged Energy Elemental")` and `mType:register(monster)` [charged_energy_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Earth Overlord")` and `mType:register(monster)` [earth_overlord.lua:Game.createMonsterType]
- `Game.createMonsterType("Energy Overlord")` and `mType:register(monster)` [energy_overlord.lua:Game.createMonsterType]
- `Game.createMonsterType("Fire Overlord")` and `mType:register(monster)` [fire_overlord.lua:Game.createMonsterType]
- `Game.createMonsterType("Flickering Spirit Elemental")` and `mType:register(monster)` [flickering_spirit_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Ice Overlord")` and `mType:register(monster)` [ice_overlord.lua:Game.createMonsterType]
- `Game.createMonsterType("Jagged Earth Elemental")` and `mType:register(monster)` [jagged_earth_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Lord of the Elements")` and `mType:register(monster)` [lord_of_the_elements.lua:Game.createMonsterType]
- `Game.createMonsterType("Muddy Earth Elemental")` and `mType:register(monster)` [muddy_earth_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Overcharged Energy Elemental")` and `mType:register(monster)` [overcharged_energy_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Psychic Spirit Elemental")` and `mType:register(monster)` [psychic_spirit_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Roaring Water Elemental")` and `mType:register(monster)` [roaring_water_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Slick Water Elemental")` and `mType:register(monster)` [slick_water_elemental.lua:Game.createMonsterType]
- `Game.createMonsterType("Spirit Overlord")` and `mType:register(monster)` [spirit_overlord.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [blazing_fire_elemental.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [blistering_fire_elemental.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [charged_energy_elemental.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [earth_overlord.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [energy_overlord.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fire_overlord.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [flickering_spirit_elemental.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ice_overlord.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [jagged_earth_elemental.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lord_of_the_elements.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [muddy_earth_elemental.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [overcharged_energy_elemental.lua:monster.flags]

## Side Effects
- Registers monster type `Blazing Fire Elemental` into the global `Game` engine registry via `mType:register(monster)` [blazing_fire_elemental.lua:mType:register]
- Registers monster type `Blistering Fire Elemental` into the global `Game` engine registry via `mType:register(monster)` [blistering_fire_elemental.lua:mType:register]
- Registers monster type `Charged Energy Elemental` into the global `Game` engine registry via `mType:register(monster)` [charged_energy_elemental.lua:mType:register]
- Registers monster type `Earth Overlord` into the global `Game` engine registry via `mType:register(monster)` [earth_overlord.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [earth_overlord.lua:monster.events]
- Registers monster type `Energy Overlord` into the global `Game` engine registry via `mType:register(monster)` [energy_overlord.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [energy_overlord.lua:monster.events]
- Registers monster type `Fire Overlord` into the global `Game` engine registry via `mType:register(monster)` [fire_overlord.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [fire_overlord.lua:monster.events]
- Registers monster type `Flickering Spirit Elemental` into the global `Game` engine registry via `mType:register(monster)` [flickering_spirit_elemental.lua:mType:register]
- Registers monster type `Ice Overlord` into the global `Game` engine registry via `mType:register(monster)` [ice_overlord.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [ice_overlord.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
