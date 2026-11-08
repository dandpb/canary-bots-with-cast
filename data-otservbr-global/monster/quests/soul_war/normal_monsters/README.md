# Normal Monsters

## Overview
Provides 17 direct files (`bony_sea_devil.lua`..`turbulent_elemental.lua`) and 3 subdirectories under `monster/quests/soul_war/normal_monsters`.

## Interface
- `Game.createMonsterType("Bony Sea Devil")` and `mType:register(monster)` [bony_sea_devil.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [bony_sea_devil.lua:mType.onThink]
- `Game.createMonsterType("Brachiodemon")` and `mType:register(monster)` [brachiodemon.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [brachiodemon.lua:mType.onThink]
- `Game.createMonsterType("Branchy Crawler")` and `mType:register(monster)` [branchy_crawler.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [branchy_crawler.lua:mType.onThink]
- `Game.createMonsterType("Capricious Phantom")` and `mType:register(monster)` [capricious_phantom.lua:Game.createMonsterType]
- `Game.createMonsterType("Distorted Phantom")` and `mType:register(monster)` [distorted_phantom.lua:Game.createMonsterType]
- Lua script module `druid's_apparition.lua` [druid's_apparition.lua:module]
- `Game.createMonsterType("Hateful Soul")` and `mType:register(monster)` [hateful_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Infernal Demon")` and `mType:register(monster)` [infernal_demon.lua:Game.createMonsterType]
- `Game.createMonsterType("Infernal Phantom")` and `mType:register(monster)` [infernal_phantom.lua:Game.createMonsterType]
- Lua script module `knight's_apparition.lua` [knight's_apparition.lua:module]
- `Game.createMonsterType("Many Faces")` and `mType:register(monster)` [many_faces.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [many_faces.lua:mType.onThink]
- Lua script module `monk's_apparition.lua` [monk's_apparition.lua:module]
- `Game.createMonsterType("Mould Phantom")` and `mType:register(monster)` [mould_phantom.lua:Game.createMonsterType]
- Lua script module `paladin's_apparition.lua` [paladin's_apparition.lua:module]
- `Game.createMonsterType("Rotten Golem")` and `mType:register(monster)` [rotten_golem.lua:Game.createMonsterType]
- Lua script module `sorcerer's_apparition.lua` [sorcerer's_apparition.lua:module]
- `Game.createMonsterType("Turbulent Elemental")` and `mType:register(monster)` [turbulent_elemental.lua:Game.createMonsterType]
- [burning_hatred](./burning_hatred/README.md) - Component package under `monster/quests/soul_war/normal_monsters/burning_hatred` containing 5 files (`ashes_of_burning_hatred.lua`..`symbol_of_hatred.lua`).
- [furious_crater](./furious_crater/README.md) - Component package under `monster/quests/soul_war/normal_monsters/furious_crater` containing 5 files (`a_greedy_eye.lua`..`vibrant_phantom.lua`).
- [megalomania_room](./megalomania_room/README.md) - Component package under `monster/quests/soul_war/normal_monsters/megalomania_room` containing 4 files (`greater_splinter_of_madness.lua`..`necromantic_focus.lua`).

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [bony_sea_devil.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bony_sea_devil.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [brachiodemon.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brachiodemon.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [branchy_crawler.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [branchy_crawler.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [capricious_phantom.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [capricious_phantom.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [distorted_phantom.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [distorted_phantom.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [hateful_soul.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [infernal_demon.lua:monster.Bestiary]

## Side Effects
- Registers monster type `Bony Sea Devil` into the global `Game` engine registry via `mType:register(monster)` [bony_sea_devil.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [bony_sea_devil.lua:monster.events]
- Registers monster type `Brachiodemon` into the global `Game` engine registry via `mType:register(monster)` [brachiodemon.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [brachiodemon.lua:monster.events]
- Registers monster type `Branchy Crawler` into the global `Game` engine registry via `mType:register(monster)` [branchy_crawler.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [branchy_crawler.lua:monster.events]
- Registers monster type `Capricious Phantom` into the global `Game` engine registry via `mType:register(monster)` [capricious_phantom.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [capricious_phantom.lua:monster.events]
- Registers monster type `Distorted Phantom` into the global `Game` engine registry via `mType:register(monster)` [distorted_phantom.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [distorted_phantom.lua:monster.events]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [druid's_apparition.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [druid's_apparition.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
