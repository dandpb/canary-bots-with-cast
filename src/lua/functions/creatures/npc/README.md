# npc

## Overview
Package implementation for `src/lua/functions/creatures/npc`, providing component logic and data interfaces for npc.

## Interface
- `NpcFunctions` (`[npc_functions.hpp:NpcFunctions]`)
- `init` (`[npc_functions.hpp:init]`)
- `luaNpcCreate` (`[npc_functions.hpp:luaNpcCreate]`)
- `luaNpcIsNpc` (`[npc_functions.hpp:luaNpcIsNpc]`)
- `luaNpcSetMasterPos` (`[npc_functions.hpp:luaNpcSetMasterPos]`)
- `luaNpcGetCurrency` (`[npc_functions.hpp:luaNpcGetCurrency]`)
- `luaNpcSetCurrency` (`[npc_functions.hpp:luaNpcSetCurrency]`)
- `luaNpcGetSpeechBubble` (`[npc_functions.hpp:luaNpcGetSpeechBubble]`)
- `ShopBlock` (`[npc_type_functions.hpp:ShopBlock]`)
- `NpcTypeFunctions` (`[npc_type_functions.hpp:NpcTypeFunctions]`)

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[npc_functions.cpp]`)
- Emits system diagnostic logs (`[npc_type_functions.cpp]`)
- Emits system diagnostic logs (`[shop_functions.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
