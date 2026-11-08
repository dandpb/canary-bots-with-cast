# npclib

## Overview
Package implementation for `data/npclib`, providing component logic and data interfaces for npclib.

## Interface
- `MsgContains` (`[npc.lua:MsgContains]`)
- `MsgFind` (`[npc.lua:MsgFind]`)
- `GetFormattedShopCategoryNames` (`[npc.lua:GetFormattedShopCategoryNames]`)
- `Npc:getRemainingShopCategories` (`[npc.lua:Npc:getRemainingShopCategories]`)
- `Npc:talk` (`[npc.lua:Npc:talk]`)
- `Npc:sendMessage` (`[npc.lua:Npc:sendMessage]`)
- `Npc:sayWithDelay` (`[npc.lua:Npc:sayWithDelay]`)
- `SayEvent` (`[npc.lua:SayEvent]`)
- Subdirectory [`./npc_system/README.md`](./npc_system/README.md) - Sub-package for npc_system

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[npc.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
