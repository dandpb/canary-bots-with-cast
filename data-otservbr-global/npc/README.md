# Npc

## Overview
Provides 1027 direct files (`....lua`..`zurak_arena.lua`) and 1 subdirectories under `npc`.

## Interface
- Defines 1027 script/configuration files (`....lua` through `zurak_arena.lua`) [....lua]
- `Game.createNpcType("...")` and `npcType:register(npcConfig)` [....lua:Game.createNpcType]
- `npcType.onThink` handler [....lua:npcType.onThink]
- `npcType.onAppear` handler [....lua:npcType.onAppear]
- `npcType.onDisappear` handler [....lua:npcType.onDisappear]
- `npcType.onMove` handler [....lua:npcType.onMove]
- `npcType.onSay` handler [....lua:npcType.onSay]
- `npcType.onCloseChannel` handler [....lua:npcType.onCloseChannel]
- `Game.createNpcType("A Bearded Woman")` and `npcType:register(npcConfig)` [a_bearded_woman.lua:Game.createNpcType]
- `npcType.onThink` handler [a_bearded_woman.lua:npcType.onThink]
- `npcType.onAppear` handler [a_bearded_woman.lua:npcType.onAppear]
- `npcType.onDisappear` handler [a_bearded_woman.lua:npcType.onDisappear]
- `npcType.onMove` handler [a_bearded_woman.lua:npcType.onMove]
- `npcType.onSay` handler [a_bearded_woman.lua:npcType.onSay]
- `npcType.onCloseChannel` handler [a_bearded_woman.lua:npcType.onCloseChannel]
- `Game.createNpcType("A Beautiful Girl")` and `npcType:register(npcConfig)` [a_beautiful_girl.lua:Game.createNpcType]
- `npcType.onThink` handler [a_beautiful_girl.lua:npcType.onThink]
- `npcType.onAppear` handler [a_beautiful_girl.lua:npcType.onAppear]
- `npcType.onDisappear` handler [a_beautiful_girl.lua:npcType.onDisappear]
- `npcType.onMove` handler [a_beautiful_girl.lua:npcType.onMove]
- `npcType.onSay` handler [a_beautiful_girl.lua:npcType.onSay]
- `npcType.onCloseChannel` handler [a_beautiful_girl.lua:npcType.onCloseChannel]
- `Game.createNpcType("A Beggar")` and `npcType:register(npcConfig)` [a_beggar.lua:Game.createNpcType]
- `npcType.onThink` handler [a_beggar.lua:npcType.onThink]
- `npcType.onAppear` handler [a_beggar.lua:npcType.onAppear]
- [blue_valley](./blue_valley/README.md) - Component package under `npc/blue_valley` containing 7 files (`bodh_the_kan.lua`..`saih_the_guardian.lua`).

## Invariants
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [....lua:npcConfig.flags]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [a_bearded_woman.lua:npcConfig.flags]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [a_beautiful_girl.lua:npcConfig.flags]
- `creatureSayCallback` requires active player focus verified by `npcHandler:checkInteraction(npc, creature)` [a_beggar.lua:creatureSayCallback]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [a_beggar.lua:npcConfig.flags]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [a_behemoth.lua:npcConfig.flags]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [a_confused_frog.lua:npcConfig.flags]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [a_dark_priestess.lua:npcConfig.flags]
- `creatureSayCallback` requires active player focus verified by `npcHandler:checkInteraction(npc, creature)` [a_dead_bureaucrat1.lua:creatureSayCallback]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [a_dead_bureaucrat1.lua:npcConfig.flags]
- `creatureSayCallback` requires active player focus verified by `npcHandler:checkInteraction(npc, creature)` [a_dead_bureaucrat2.lua:creatureSayCallback]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [a_dead_bureaucrat2.lua:npcConfig.flags]

## Side Effects
- Registers NPC `...` into the `Game` engine via `npcType:register(npcConfig)` [....lua:npcType:register]
- Registers NPC `A Bearded Woman` into the `Game` engine via `npcType:register(npcConfig)` [a_bearded_woman.lua:npcType:register]
- Registers NPC `A Beautiful Girl` into the `Game` engine via `npcType:register(npcConfig)` [a_beautiful_girl.lua:npcType:register]
- Registers NPC `A Beggar` into the `Game` engine via `npcType:register(npcConfig)` [a_beggar.lua:npcType:register]
- Updates player quest and dialogue state via `player:setStorageValue` [a_beggar.lua:creatureSayCallback]
- Registers NPC `A Behemoth` into the `Game` engine via `npcType:register(npcConfig)` [a_behemoth.lua:npcType:register]
- Updates player quest and dialogue state via `player:setStorageValue` [a_behemoth.lua:creatureSayCallback]
- Registers NPC `A Confused Frog` into the `Game` engine via `npcType:register(npcConfig)` [a_confused_frog.lua:npcType:register]
- Registers NPC `A Dark Priestess` into the `Game` engine via `npcType:register(npcConfig)` [a_dark_priestess.lua:npcType:register]
- Registers NPC `A Dead Bureaucrat` into the `Game` engine via `npcType:register(npcConfig)` [a_dead_bureaucrat1.lua:npcType:register]
- Updates player quest and dialogue state via `player:setStorageValue` [a_dead_bureaucrat1.lua:creatureSayCallback]
- Registers NPC `A Dead Bureaucrat` into the `Game` engine via `npcType:register(npcConfig)` [a_dead_bureaucrat2.lua:npcType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
