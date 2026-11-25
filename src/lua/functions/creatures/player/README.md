# player

## Overview
Package implementation for `src/lua/functions/creatures/player`, providing component logic and data interfaces for player.

## Interface
- `GroupFunctions` (`[group_functions.hpp:GroupFunctions]`)
- `init` (`[group_functions.hpp:init]`)
- `luaGroupCreate` (`[group_functions.hpp:luaGroupCreate]`)
- `luaGroupGetId` (`[group_functions.hpp:luaGroupGetId]`)
- `luaGroupGetName` (`[group_functions.hpp:luaGroupGetName]`)
- `luaGroupGetFlags` (`[group_functions.hpp:luaGroupGetFlags]`)
- `luaGroupGetAccess` (`[group_functions.hpp:luaGroupGetAccess]`)
- `luaGroupGetMaxDepotItems` (`[group_functions.hpp:luaGroupGetMaxDepotItems]`)
- `GuildFunctions` (`[guild_functions.hpp:GuildFunctions]`)
- `MountFunctions` (`[mount_functions.hpp:MountFunctions]`)
- `PartyFunctions` (`[party_functions.hpp:PartyFunctions]`)
- `PlayerFunctions` (`[player_functions.hpp:PlayerFunctions]`, `[player_functions.cpp:PlayerFunctions::init]`): Registers `Player` Lua methods including paginated container batching (`luaPlayerAddItemBatchToPaginedContainer`), `getBackpack`, `getLootPouch`, coin transfers/redemption, imbuement scrolls (`luaPlayerApplyImbuementScroll`, `luaPlayerClearAllImbuements`), PvP mode (`luaPlayerGetPvpMode`, `luaPlayerHasAttacked`), food (`luaPlayerUpdateFood`), race icon overlays (`luaPlayerSetRaceIconOverlay`, `luaPlayerClearRaceIconOverlays`, `luaPlayerRefreshVisibleCreatureIcons`), weapon proficiency (`luaPlayerAddWeaponExperience`), and livestream viewer APIs (`luaPlayerGetLivestreamViewersCount`, `luaPlayerGetLivestreamViewers`, `luaPlayerSetLivestreamViewers`, `luaPlayerIsLivestreamViewer`).
- `VocationFunctions` (`[vocation_functions.hpp:VocationFunctions]`)

## Invariants
- None

## Side Effects
- None

## Verification
- See the [C++ build and test guide](../../../../../tests/README.md#running-tests).
