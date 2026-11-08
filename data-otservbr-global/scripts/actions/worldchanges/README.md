# Worldchanges

## Overview
Intermediate blueprint grouping 2 subdirectories under `scripts/actions/worldchanges`.

## Subdirectories & Boundaries
- [deeplings](./deeplings/README.md) - Component package under `scripts/actions/worldchanges/deeplings` containing 1 files (`bosses_reward.lua`..`bosses_reward.lua`).
- [the_mummys_curse](./the_mummys_curse/README.md) - Component package under `scripts/actions/worldchanges/the_mummys_curse` containing 1 files (`horestis_jars.lua`..`horestis_jars.lua`).

## Interface
- `bossesReward.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [bosses_reward.lua:bossesReward.onUse]
- `Action()` assigned to `bossesReward` [bosses_reward.lua:bossesReward]
- `createWall()` [horestis_jars.lua:createWall]
- `horestisJars.onUse(cid, item, fromPosition, itemEx, toPosition)` [horestis_jars.lua:horestisJars.onUse]
- [deeplings](./deeplings/README.md) - Component package under `scripts/actions/worldchanges/deeplings` containing 1 files (`bosses_reward.lua`..`bosses_reward.lua`).
- [the_mummys_curse](./the_mummys_curse/README.md) - Component package under `scripts/actions/worldchanges/the_mummys_curse` containing 1 files (`horestis_jars.lua`..`horestis_jars.lua`).

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [bosses_reward.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [bosses_reward.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [horestis_jars.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
