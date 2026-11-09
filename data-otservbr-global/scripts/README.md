# Scripts

## Overview
Intermediate blueprint grouping 14 subdirectories under `scripts`.

## Subdirectories & Boundaries
- [actions](./actions/README.md) - Intermediate blueprint grouping 18 subdirectories under `scripts/actions`.
- [blue_valley](./blue_valley/README.md) - Component package under `scripts/blue_valley` containing 1 files (`monk_npcs_step_in.lua`..`monk_npcs_step_in.lua`).
- [creaturescripts](./creaturescripts/README.md) - Intermediate blueprint grouping 3 subdirectories under `scripts/creaturescripts`.
- [custom](./custom/README.md) - Component package under `scripts/custom` containing 4 files (`ambient_sounds.lua`..`movement_trainer_exit.lua`).
- [game_migrations](./game_migrations/README.md) - Component package under `scripts/game_migrations` containing 5 files (`20231128213358_move_hireling_data_to_kv.lua`..`20251737599334_reset_old_charms.lua`).
- [globalevents](./globalevents/README.md) - Provides 2 direct files (`dawnport_magic_effect.lua`..`update.lua`) and 3 subdirectories under `scripts/globalevents`.
- [lib](./lib/README.md) - Component package under `scripts/lib` containing 2 files (`monster_functions.lua`..`register_actions.lua`).
- [movements](./movements/README.md) - Intermediate blueprint grouping 5 subdirectories under `scripts/movements`.
- [quests](./quests/README.md) - Intermediate blueprint grouping 114 subdirectories under `scripts/quests`.
- [raids](./raids/README.md) - Intermediate blueprint grouping 3 subdirectories under `scripts/raids`.
- [spells](./spells/README.md) - Intermediate blueprint grouping 1 subdirectories under `scripts/spells`.
- [systems](./systems/README.md) - Component package under `scripts/systems` containing 1 files (`hazard_primal.lua`..`hazard_primal.lua`).
- [talkactions](./talkactions/README.md) - Intermediate blueprint grouping 1 subdirectories under `scripts/talkactions`.
- [world_changes](./world_changes/README.md) - Component package under `scripts/world_changes` containing 6 files (`fury_gates.lua`..`their_masters_voice.lua`).

## Interface
- `doNotTeleport(player)` [adventurers_stone.lua:doNotTeleport]
- `adventurersStone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [adventurers_stone.lua:adventurersStone.onUse]
- `shouldSayMessage(pos, fromPos)` [monk_npcs_step_in.lua:shouldSayMessage]
- `monkGate.onStepIn(creature, item, position, fromPosition)` [monk_npcs_step_in.lua:monkGate.onStepIn]
- `playerFreeQuestStart(playerId, index)` [freequests.lua:playerFreeQuestStart]
- `freeQuests.onLogin(player)` [freequests.lua:freeQuests.onLogin]
- `getCurrentSound(zoneData, period)` [ambient_sounds.lua:getCurrentSound]
- `getEffectivePeriod()` [ambient_sounds.lua:getEffectivePeriod]
- `getOutfits(player)` [20231128213358_move_hireling_data_to_kv.lua:getOutfits]
- `getSkills(player)` [20231128213358_move_hireling_data_to_kv.lua:getSkills]
- `dawnportMagicEffect.onThink(interval)` [dawnport_magic_effect.lua:dawnportMagicEffect.onThink]
- `GlobalEvent("DawnportMagicEffect")` assigned to `dawnportMagicEffect` [dawnport_magic_effect.lua:dawnportMagicEffect]
- `Monster:handleCobraOnSpawn()` [monster_functions.lua:Monster:handleCobraOnSpawn]
- `revertItem(position, itemId, transformId)` [register_actions.lua:revertItem]
- `oramondEntrance.onStepIn(creature, item, position, fromPosition)` [oramond_entrance.lua:oramondEntrance.onStepIn]
- `MoveEvent()` assigned to `oramondEntrance` [oramond_entrance.lua:oramondEntrance]
- `action.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_cheesy_key.lua:action.onUse]
- `Action()` assigned to `action` [actions_cheesy_key.lua:action]
- `Raid("drefia.arachir", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` assigned to `raid` [arachir_the_ancient_one.lua:raid]
- `Raid("drefia.arachir", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` registration [arachir_the_ancient_one.lua:Raid]
- Defines 591 script/configuration files (`abyssador_paralyze.lua` through `zushuka_paralyze.lua`) [abyssador_paralyze.lua]
- `spell.onCastSpell(creature, var)` [abyssador_paralyze.lua:spell.onCastSpell]
- `primalPod.onStepIn(creature, item, position, fromPosition)` [hazard_primal.lua:primalPod.onStepIn]
- `createPrimalPod(position)` [hazard_primal.lua:createPrimalPod]
- `loadConfig()` [house_backfill.lua:loadConfig]
- [actions](./actions/README.md) - Intermediate blueprint grouping 18 subdirectories under `scripts/actions`.
- [blue_valley](./blue_valley/README.md) - Component package under `scripts/blue_valley` containing 1 files (`monk_npcs_step_in.lua`..`monk_npcs_step_in.lua`).
- [creaturescripts](./creaturescripts/README.md) - Intermediate blueprint grouping 3 subdirectories under `scripts/creaturescripts`.
- [custom](./custom/README.md) - Component package under `scripts/custom` containing 4 files (`ambient_sounds.lua`..`movement_trainer_exit.lua`).
- [game_migrations](./game_migrations/README.md) - Component package under `scripts/game_migrations` containing 5 files (`20231128213358_move_hireling_data_to_kv.lua`..`20251737599334_reset_old_charms.lua`).
- [globalevents](./globalevents/README.md) - Provides 2 direct files (`dawnport_magic_effect.lua`..`update.lua`) and 3 subdirectories under `scripts/globalevents`.
- [lib](./lib/README.md) - Component package under `scripts/lib` containing 2 files (`monster_functions.lua`..`register_actions.lua`).
- [movements](./movements/README.md) - Intermediate blueprint grouping 5 subdirectories under `scripts/movements`.
- [quests](./quests/README.md) - Intermediate blueprint grouping 114 subdirectories under `scripts/quests`.
- [raids](./raids/README.md) - Intermediate blueprint grouping 3 subdirectories under `scripts/raids`.
- [spells](./spells/README.md) - Intermediate blueprint grouping 1 subdirectories under `scripts/spells`.
- [systems](./systems/README.md) - Component package under `scripts/systems` containing 1 files (`hazard_primal.lua`..`hazard_primal.lua`).
- [talkactions](./talkactions/README.md) - Intermediate blueprint grouping 1 subdirectories under `scripts/talkactions`.
- [world_changes](./world_changes/README.md) - Component package under `scripts/world_changes` containing 6 files (`fury_gates.lua`..`their_masters_voice.lua`).

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [adventurers_stone.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [monk_npcs_step_in.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [freequests.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [ambient_sounds.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [20231128213358_move_hireling_data_to_kv.lua:getStorageValue]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [update.lua:db.query]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [monster_functions.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [oramond_entrance.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_rascacoon_shortcut.lua:getPlayer]
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [abyssador_paralyze.lua:combat]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [hazard_primal.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [house_backfill.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [adventurers_stone.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [monk_npcs_step_in.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [freequests.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [ambient_sounds.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [20231128213358_move_hireling_data_to_kv.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [dawnport_magic_effect.lua:register]
- Mutates player or global storage state via `setStorageValue` [monster_functions.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [oramond_entrance.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_cheesy_key.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [arachir_the_ancient_one.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [abyssador_paralyze.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [hazard_primal.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
