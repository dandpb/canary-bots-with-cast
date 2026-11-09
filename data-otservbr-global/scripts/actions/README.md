# Actions

## Overview
Intermediate blueprint grouping 18 subdirectories under `scripts/actions`.

## Subdirectories & Boundaries
- [adventurers_guild](./adventurers_guild/README.md) - Component package under `scripts/actions/adventurers_guild` containing 2 files (`adventurers_stone.lua`..`magic_door.lua`).
- [arena_pvp](./arena_pvp/README.md) - Component package under `scripts/actions/arena_pvp` containing 2 files (`arena_10x10.lua`..`arena_2x2.lua`).
- [dawnport](./dawnport/README.md) - Component package under `scripts/actions/dawnport` containing 2 files (`lever.lua`..`vocation_door.lua`).
- [falcons](./falcons/README.md) - Component package under `scripts/actions/falcons` containing 1 files (`falcon_shield.lua`..`falcon_shield.lua`).
- [farmine](./farmine/README.md) - Component package under `scripts/actions/farmine` containing 1 files (`temple_of_equilibrium_vines.lua`..`temple_of_equilibrium_vines.lua`).
- [kazordoon](./kazordoon/README.md) - Component package under `scripts/actions/kazordoon` containing 4 files (`elevator_lever.lua`..`trap_door.lua`).
- [mounts](./mounts/README.md) - Component package under `scripts/actions/mounts` containing 1 files (`mounts.lua`..`mounts.lua`).
- [object](./object/README.md) - Component package under `scripts/actions/object` containing 7 files (`dancingfairy.lua`..`wz789_entrance.lua`).
- [oramond](./oramond/README.md) - Component package under `scripts/actions/oramond` containing 5 files (`elevator.lua`..`teleport_west.lua`).
- [other](./other/README.md) - Provides 29 direct files (`baking.lua`..`world_board.lua`) and 1 subdirectories under `scripts/actions/other`.
- [rookgaard](./rookgaard/README.md) - Provides 4 direct files (`chest.lua`..`sewer_lever.lua`) and 2 subdirectories under `scripts/actions/rookgaard`.
- [roshamuul](./roshamuul/README.md) - Intermediate blueprint grouping 1 subdirectories under `scripts/actions/roshamuul`.
- [shrines](./shrines/README.md) - Component package under `scripts/actions/shrines` containing 1 files (`feyrist_exit.lua`..`feyrist_exit.lua`).
- [soulpit](./soulpit/README.md) - Component package under `scripts/actions/soulpit` containing 2 files (`soulpit_arena_exit.lua`..`soulpit_entrance.lua`).
- [system](./system/README.md) - Component package under `scripts/actions/system` containing 1 files (`quest_reward_common.lua`..`quest_reward_common.lua`).
- [tools](./tools/README.md) - Component package under `scripts/actions/tools` containing 11 files (`bricklayer_kit.lua`..`spiked_squelcher.lua`).
- [valuables](./valuables/README.md) - Component package under `scripts/actions/valuables` containing 1 files (`random_items.lua`..`random_items.lua`).
- [worldchanges](./worldchanges/README.md) - Intermediate blueprint grouping 2 subdirectories under `scripts/actions/worldchanges`.

## Interface
- `doNotTeleport(player)` [adventurers_stone.lua:doNotTeleport]
- `adventurersStone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [adventurers_stone.lua:adventurersStone.onUse]
- `arena10x10.onUse(player, item, fromPosition, target, toPosition, monster, isHotkey)` [arena_10x10.lua:arena10x10.onUse]
- `Action()` assigned to `arena10x10` [arena_10x10.lua:arena10x10]
- `lever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [lever.lua:lever.onUse]
- `Action()` assigned to `lever` [lever.lua:lever]
- `falconShield.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [falcon_shield.lua:falconShield.onUse]
- `Action()` assigned to `falconShield` [falcon_shield.lua:falconShield]
- `templeOfEquilibriumVines.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [temple_of_equilibrium_vines.lua:templeOfEquilibriumVines.onUse]
- `Action()` assigned to `templeOfEquilibriumVines` [temple_of_equilibrium_vines.lua:templeOfEquilibriumVines]
- `elevatorLever.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [elevator_lever.lua:elevatorLever.onUse]
- `Action()` assigned to `elevatorLever` [elevator_lever.lua:elevatorLever]
- `doFailAction(cid, mount, pos, item, itemEx, loseItem)` [mounts.lua:doFailAction]
- `mounts.onUse(cid, item, fromPosition, itemEx, toPosition)` [mounts.lua:mounts.onUse]
- `dancingfairy.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [dancingfairy.lua:dancingfairy.onUse]
- `Action()` assigned to `dancingfairy` [dancingfairy.lua:dancingfairy]
- `elevator.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [elevator.lua:elevator.onUse]
- `Action()` assigned to `elevator` [elevator.lua:elevator]
- Defines 29 script/configuration files (`baking.lua` through `world_board.lua`) [baking.lua]
- `baking.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [baking.lua:baking.onUse]
- `chest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [chest.lua:chest.onUse]
- `Action()` assigned to `chest` [chest.lua:chest]
- `golden.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [golden.lua:golden.onUse]
- `Action()` assigned to `golden` [golden.lua:golden]
- `feyristExit.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [feyrist_exit.lua:feyristExit.onUse]
- [adventurers_guild](./adventurers_guild/README.md) - Component package under `scripts/actions/adventurers_guild` containing 2 files (`adventurers_stone.lua`..`magic_door.lua`).
- [arena_pvp](./arena_pvp/README.md) - Component package under `scripts/actions/arena_pvp` containing 2 files (`arena_10x10.lua`..`arena_2x2.lua`).
- [dawnport](./dawnport/README.md) - Component package under `scripts/actions/dawnport` containing 2 files (`lever.lua`..`vocation_door.lua`).
- [falcons](./falcons/README.md) - Component package under `scripts/actions/falcons` containing 1 files (`falcon_shield.lua`..`falcon_shield.lua`).
- [farmine](./farmine/README.md) - Component package under `scripts/actions/farmine` containing 1 files (`temple_of_equilibrium_vines.lua`..`temple_of_equilibrium_vines.lua`).
- [kazordoon](./kazordoon/README.md) - Component package under `scripts/actions/kazordoon` containing 4 files (`elevator_lever.lua`..`trap_door.lua`).
- [mounts](./mounts/README.md) - Component package under `scripts/actions/mounts` containing 1 files (`mounts.lua`..`mounts.lua`).
- [object](./object/README.md) - Component package under `scripts/actions/object` containing 7 files (`dancingfairy.lua`..`wz789_entrance.lua`).
- [oramond](./oramond/README.md) - Component package under `scripts/actions/oramond` containing 5 files (`elevator.lua`..`teleport_west.lua`).
- [other](./other/README.md) - Provides 29 direct files (`baking.lua`..`world_board.lua`) and 1 subdirectories under `scripts/actions/other`.
- [rookgaard](./rookgaard/README.md) - Provides 4 direct files (`chest.lua`..`sewer_lever.lua`) and 2 subdirectories under `scripts/actions/rookgaard`.
- [roshamuul](./roshamuul/README.md) - Intermediate blueprint grouping 1 subdirectories under `scripts/actions/roshamuul`.
- [shrines](./shrines/README.md) - Component package under `scripts/actions/shrines` containing 1 files (`feyrist_exit.lua`..`feyrist_exit.lua`).
- [soulpit](./soulpit/README.md) - Component package under `scripts/actions/soulpit` containing 2 files (`soulpit_arena_exit.lua`..`soulpit_entrance.lua`).
- [system](./system/README.md) - Component package under `scripts/actions/system` containing 1 files (`quest_reward_common.lua`..`quest_reward_common.lua`).
- [tools](./tools/README.md) - Component package under `scripts/actions/tools` containing 11 files (`bricklayer_kit.lua`..`spiked_squelcher.lua`).
- [valuables](./valuables/README.md) - Component package under `scripts/actions/valuables` containing 1 files (`random_items.lua`..`random_items.lua`).
- [worldchanges](./worldchanges/README.md) - Intermediate blueprint grouping 2 subdirectories under `scripts/actions/worldchanges`.

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [adventurers_stone.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [arena_10x10.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [lever.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [elevator_lever.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [dancingfairy.lua:Tile]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [elevator.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [construction_kits.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [chest.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [golden.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [soulpit_entrance.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [quest_reward_common.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [hammer.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [adventurers_stone.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [arena_10x10.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [lever.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [falcon_shield.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [temple_of_equilibrium_vines.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [elevator_lever.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [mounts.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [dancingfairy.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [elevator.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [baking.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [chest.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [golden.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
