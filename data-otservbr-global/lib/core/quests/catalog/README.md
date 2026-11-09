# Catalog

## Overview
Component package under `lib/core/quests/catalog` containing 52 files (`001_the_queen_of_the_banshees.lua`..`init.lua`).

## Interface
- Defines 52 script/configuration files (`001_the_queen_of_the_banshees.lua` through `init.lua`) [001_the_queen_of_the_banshees.lua]
- Lua script module `001_the_queen_of_the_banshees.lua` [001_the_queen_of_the_banshees.lua:module]
- Lua script module `002_the_paradox_tower.lua` [002_the_paradox_tower.lua:module]
- Lua script module `003_spike_task.lua` [003_spike_task.lua:module]
- Lua script module `004_a_father_s_burden.lua` [004_a_father_s_burden.lua:module]
- Lua script module `005_bigfoot_s_burden.lua` [005_bigfoot_s_burden.lua:module]
- Lua script module `006_children_of_the_revolution.lua` [006_children_of_the_revolution.lua:module]
- Lua script module `007_factions.lua` [007_factions.lua:module]
- Lua script module `008_friends_and_traders.lua` [008_friends_and_traders.lua:module]
- Lua script module `009_hot_cuisine.lua` [009_hot_cuisine.lua:module]
- Lua script module `010_in_service_of_yalahar.lua` [010_in_service_of_yalahar.lua:module]
- Lua script module `011_killing_in_the_name_of.lua` [011_killing_in_the_name_of.lua:module]
- Lua script module `012_outfit_and_addon_quests.lua` [012_outfit_and_addon_quests.lua:module]
- Lua script module `013_sam_s_old_backpack.lua` [013_sam_s_old_backpack.lua:module]
- Lua script module `014_sea_of_light.lua` [014_sea_of_light.lua:module]
- Lua script module `015_secret_service.lua` [015_secret_service.lua:module]
- Lua script module `016_the_ancient_tombs.lua` [016_the_ancient_tombs.lua:module]
- Lua script module `017_the_ape_city.lua` [017_the_ape_city.lua:module]
- Lua script module `018_the_beginning.lua` [018_the_beginning.lua:module]
- Lua script module `019_the_djinn_war_efreet_faction.lua` [019_the_djinn_war_efreet_faction.lua:module]
- Lua script module `020_the_djinn_war_marid_faction.lua` [020_the_djinn_war_marid_faction.lua:module]
- Lua script module `021_the_hidden_city_of_beregar.lua` [021_the_hidden_city_of_beregar.lua:module]
- Lua script module `022_the_ice_islands_quest.lua` [022_the_ice_islands_quest.lua:module]
- Lua script module `023_the_inquisition.lua` [023_the_inquisition.lua:module]
- Lua script module `024_the_postman_missions.lua` [024_the_postman_missions.lua:module]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [003_spike_task.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [005_bigfoot_s_burden.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [011_killing_in_the_name_of.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [031_tibia_tales.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [034_wrath_of_the_emperor.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [037_the_first_dragon.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [038_cults_of_tibia.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [039_dangerous_depths.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [040_adventurers_guild.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [041_dawnport.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [042_the_rookie_guard.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [045_threatened_dreams.lua:getStorageValue]

## Side Effects
- Loads and executes `CORE_DIRECTORY .. "/lib/core/quests/catalog.lua"` via `dofile` [init.lua:dofile]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
