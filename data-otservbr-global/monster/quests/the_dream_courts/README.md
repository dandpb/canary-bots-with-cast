# The Dream Courts

## Overview
Provides 12 direct files (`generator.lua`..`whirling_blades.lua`) and 1 subdirectories under `monster/quests/the_dream_courts`.

## Interface
- `Game.createMonsterType("Generator")` and `mType:register(monster)` [generator.lua:Game.createMonsterType]
- `Game.createMonsterType("Horrible Dream")` and `mType:register(monster)` [horrible_dream.lua:Game.createMonsterType]
- `Game.createMonsterType("Lucifuga Aranea")` and `mType:register(monster)` [lucifuga_aranea.lua:Game.createMonsterType]
- `Game.createMonsterType("Mind-Wrecking Dream")` and `mType:register(monster)` [mind-wrecking_dream.lua:Game.createMonsterType]
- `Game.createMonsterType("Nightmare Tendril")` and `mType:register(monster)` [nightmare_tendril.lua:Game.createMonsterType]
- `Game.createMonsterType("Nightmarish Dream")` and `mType:register(monster)` [nightmarish_dream.lua:Game.createMonsterType]
- `Game.createMonsterType("Plant Abomination")` and `mType:register(monster)` [plant_abomination.lua:Game.createMonsterType]
- `Game.createMonsterType("Plant Attendant")` and `mType:register(monster)` [plant_attendant.lua:Game.createMonsterType]
- `Game.createMonsterType("The Cold of Winter")` and `mType:register(monster)` [the_cold_of_winter.lua:Game.createMonsterType]
- `Game.createMonsterType("The Heat of Summer")` and `mType:register(monster)` [the_heat_of_summer.lua:Game.createMonsterType]
- `Game.createMonsterType("Unpleasant Dream")` and `mType:register(monster)` [unpleasant_dream.lua:Game.createMonsterType]
- `Game.createMonsterType("Whirling Blades")` and `mType:register(monster)` [whirling_blades.lua:Game.createMonsterType]
- [bosses](./bosses/README.md) - Component package under `monster/quests/the_dream_courts/bosses` containing 7 files (`alptramun.lua`..`the_nightmare_beast.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [generator.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [horrible_dream.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lucifuga_aranea.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mind-wrecking_dream.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [nightmare_tendril.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [nightmarish_dream.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [plant_abomination.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [plant_attendant.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_cold_of_winter.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [the_heat_of_summer.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [unpleasant_dream.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [whirling_blades.lua:monster.flags]

## Side Effects
- Registers monster type `Generator` into the global `Game` engine registry via `mType:register(monster)` [generator.lua:mType:register]
- Registers monster type `Horrible Dream` into the global `Game` engine registry via `mType:register(monster)` [horrible_dream.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [horrible_dream.lua:monster.events]
- Registers monster type `Lucifuga Aranea` into the global `Game` engine registry via `mType:register(monster)` [lucifuga_aranea.lua:mType:register]
- Registers monster type `Mind-Wrecking Dream` into the global `Game` engine registry via `mType:register(monster)` [mind-wrecking_dream.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [mind-wrecking_dream.lua:monster.events]
- Registers monster type `Nightmare Tendril` into the global `Game` engine registry via `mType:register(monster)` [nightmare_tendril.lua:mType:register]
- Registers monster type `Nightmarish Dream` into the global `Game` engine registry via `mType:register(monster)` [nightmarish_dream.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [nightmarish_dream.lua:monster.events]
- Registers monster type `Plant Abomination` into the global `Game` engine registry via `mType:register(monster)` [plant_abomination.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [plant_abomination.lua:monster.events]
- Registers monster type `Plant Attendant` into the global `Game` engine registry via `mType:register(monster)` [plant_attendant.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
