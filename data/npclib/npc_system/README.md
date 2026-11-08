# npc_system

## Overview
Package implementation for `data/npclib/npc_system`, providing component logic and data interfaces for npc_system.

## Interface
- `Npc:parseBankMessages` (`[bank_system.lua:Npc:parseBankMessages]`)
- `Npc:parseBank` (`[bank_system.lua:Npc:parseBank]`)
- `Npc:parseGuildBank` (`[bank_system.lua:Npc:parseGuildBank]`)
- `NpcBankGreetCallback` (`[bank_system.lua:NpcBankGreetCallback]`)
- `StdModule.travelDiscount` (`[custom_modules.lua:StdModule.travelDiscount]`)
- `StdModule.kick` (`[custom_modules.lua:StdModule.kick]`)
- `GreetModule.greet` (`[custom_modules.lua:GreetModule.greet]`)
- `GreetModule.farewell` (`[custom_modules.lua:GreetModule.farewell]`)
- `KeywordHandler:addGreetKeyword` (`[custom_modules.lua:KeywordHandler:addGreetKeyword]`)
- `KeywordHandler:addCustomGreetKeyword` (`[custom_modules.lua:KeywordHandler:addCustomGreetKeyword]`)

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[npc_handler.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
