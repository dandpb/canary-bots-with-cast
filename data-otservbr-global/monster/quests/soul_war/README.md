# Soul War

## Overview
Provides 23 direct files (`aspect_of_power.lua`..`weeping_soul.lua`) and 1 subdirectories under `monster/quests/soul_war`.

## Interface
- `Game.createMonsterType("Aspect of Power")` and `mType:register(monster)` [aspect_of_power.lua:Game.createMonsterType]
- `Game.createMonsterType("Dreadful Disruptor")` and `mType:register(monster)` [dreadful_disruptor.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [dreadful_disruptor.lua:mType.onThink]
- `mType.onAppear` lifecycle callback [dreadful_disruptor.lua:mType.onAppear]
- `mType.onDisappear` lifecycle callback [dreadful_disruptor.lua:mType.onDisappear]
- `mType.onMove` lifecycle callback [dreadful_disruptor.lua:mType.onMove]
- `mType.onSay` lifecycle callback [dreadful_disruptor.lua:mType.onSay]
- `Game.createMonsterType("Dreadful Harvester")` and `mType:register(monster)` [dreadful_harvester.lua:Game.createMonsterType]
- Lua script module `goshnar's_megalomania_blue.lua` [goshnar's_megalomania_blue.lua:module]
- Lua script module `goshnar's_megalomania_green.lua` [goshnar's_megalomania_green.lua:module]
- Lua script module `goshnar's_megalomania_purple.lua` [goshnar's_megalomania_purple.lua:module]
- Lua script module `goshnars_cruelty.lua` [goshnars_cruelty.lua:module]
- Lua script module `goshnars_greed.lua` [goshnars_greed.lua:module]
- Lua script module `goshnars_hatred.lua` [goshnars_hatred.lua:module]
- Lua script module `goshnars_malice.lua` [goshnars_malice.lua:module]
- Lua script module `goshnars_spite.lua` [goshnars_spite.lua:module]
- `Game.createMonsterType("Greedbeast")` and `mType:register(monster)` [greedbeast.lua:Game.createMonsterType]
- `Game.createMonsterType("Malicious Soul")` and `mType:register(monster)` [malicious_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Mean Maw")` and `mType:register(monster)` [mean_maw.lua:Game.createMonsterType]
- `Game.createMonsterType("Mirror Image")` and `mType:register(monster)` [mirror_image.lua:Game.createMonsterType]
- `Game.createMonsterType("Powerful Soul")` and `mType:register(monster)` [powerful_soul.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [powerful_soul.lua:mType.onThink]
- `Game.createMonsterType("Soul Cage")` and `mType:register(monster)` [soul_cage.lua:Game.createMonsterType]
- `Game.createMonsterType("Soul Sphere")` and `mType:register(monster)` [soul_sphere.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [soul_sphere.lua:mType.onThink]
- [normal_monsters](./normal_monsters/README.md) - Provides 17 direct files (`bony_sea_devil.lua`..`turbulent_elemental.lua`) and 3 subdirectories under `monster/quests/soul_war/normal_monsters`.

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [aspect_of_power.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dreadful_disruptor.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dreadful_harvester.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [greedbeast.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [malicious_soul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mean_maw.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mirror_image.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [powerful_soul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [soul_cage.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [soul_sphere.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [soulsnatcher.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [spiteful_spitter.lua:monster.flags]

## Side Effects
- Registers monster type `Aspect of Power` into the global `Game` engine registry via `mType:register(monster)` [aspect_of_power.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [aspect_of_power.lua:monster.events]
- Registers monster type `Dreadful Disruptor` into the global `Game` engine registry via `mType:register(monster)` [dreadful_disruptor.lua:mType:register]
- Registers monster type `Dreadful Harvester` into the global `Game` engine registry via `mType:register(monster)` [dreadful_harvester.lua:mType:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [goshnar's_megalomania_blue.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [goshnar's_megalomania_blue.lua:Game]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [goshnar's_megalomania_green.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [goshnar's_megalomania_green.lua:Game]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [goshnar's_megalomania_purple.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [goshnar's_megalomania_purple.lua:Game]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [goshnars_cruelty.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [goshnars_cruelty.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
