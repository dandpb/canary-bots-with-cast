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
- `init` (`[guild_functions.hpp:init]`)

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
