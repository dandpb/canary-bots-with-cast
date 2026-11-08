# Game Migrations

## Overview
Component package under `scripts/game_migrations` containing 5 files (`20231128213358_move_hireling_data_to_kv.lua`..`20251737599334_reset_old_charms.lua`).

## Interface
- `getOutfits(player)` [20231128213358_move_hireling_data_to_kv.lua:getOutfits]
- `getSkills(player)` [20231128213358_move_hireling_data_to_kv.lua:getSkills]
- `migrateHirelingData(player)` [20231128213358_move_hireling_data_to_kv.lua:migrateHirelingData]
- `migration:onExecute()` [20231128213358_move_hireling_data_to_kv.lua:migration:onExecute]
- `Migration("20231128213158_move_hireling_data_to_kv")` assigned to `migration` [20231128213358_move_hireling_data_to_kv.lua:migration]
- `Migration("20231128213158_move_hireling_data_to_kv")` registration [20231128213358_move_hireling_data_to_kv.lua:Migration]
- `migrateAchievementProgress(player)` [20241708000535_move_achievement_to_kv.lua:migrateAchievementProgress]
- `migration:onExecute()` [20241708000535_move_achievement_to_kv.lua:migration:onExecute]
- `Migration("20241708000535_move_achievement_to_kv")` assigned to `migration` [20241708000535_move_achievement_to_kv.lua:migration]
- `Migration("20241708000535_move_achievement_to_kv")` registration [20241708000535_move_achievement_to_kv.lua:Migration]
- `migrateIsVipSystem(player)` [20241708362079_move_vip_system_to_kv.lua:migrateIsVipSystem]
- `migration:onExecute()` [20241708362079_move_vip_system_to_kv.lua:migration:onExecute]
- `Migration("20241708362079_move_vip_system_to_kv")` assigned to `migration` [20241708362079_move_vip_system_to_kv.lua:migration]
- `Migration("20241708362079_move_vip_system_to_kv")` registration [20241708362079_move_vip_system_to_kv.lua:Migration]
- `migrate(player)` [20241715984294_quests_storages_to_kv.lua:migrate]
- `migration:onExecute()` [20241715984294_quests_storages_to_kv.lua:migration:onExecute]
- `Migration("20241715984294_quests_storages_to_kv")` assigned to `migration` [20241715984294_quests_storages_to_kv.lua:migration]
- `Migration("20241715984294_quests_storages_to_kv")` registration [20241715984294_quests_storages_to_kv.lua:Migration]
- `migration:onExecute()` [20251737599334_reset_old_charms.lua:migration:onExecute]
- `Migration("20251737599334_reset_charms")` assigned to `migration` [20251737599334_reset_old_charms.lua:migration]
- `Migration("20251737599334_reset_charms")` registration [20251737599334_reset_old_charms.lua:Migration]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [20231128213358_move_hireling_data_to_kv.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [20241708000535_move_achievement_to_kv.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [20241708362079_move_vip_system_to_kv.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [20241715984294_quests_storages_to_kv.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [20231128213358_move_hireling_data_to_kv.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [20241708000535_move_achievement_to_kv.lua:register]
- Mutates player or global storage state via `setStorageValue` [20241708000535_move_achievement_to_kv.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [20241708362079_move_vip_system_to_kv.lua:register]
- Mutates player or global storage state via `setStorageValue` [20241708362079_move_vip_system_to_kv.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [20241715984294_quests_storages_to_kv.lua:register]
- Mutates player or global storage state via `setStorageValue` [20241715984294_quests_storages_to_kv.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [20251737599334_reset_old_charms.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
