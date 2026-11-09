# Blue Valley

## Overview
Component package under `npc/blue_valley` containing 7 files (`bodh_the_kan.lua`..`saih_the_guardian.lua`).

## Interface
- `Game.createNpcType("Bodh The Kan")` and `npcType:register(npcConfig)` [bodh_the_kan.lua:Game.createNpcType]
- `npcType.onThink` handler [bodh_the_kan.lua:npcType.onThink]
- `npcType.onAppear` handler [bodh_the_kan.lua:npcType.onAppear]
- `npcType.onDisappear` handler [bodh_the_kan.lua:npcType.onDisappear]
- `npcType.onMove` handler [bodh_the_kan.lua:npcType.onMove]
- `npcType.onSay` handler [bodh_the_kan.lua:npcType.onSay]
- `npcType.onCloseChannel` handler [bodh_the_kan.lua:npcType.onCloseChannel]
- `Game.createNpcType("Chesa The Guardian")` and `npcType:register(npcConfig)` [chesa_the_guardian.lua:Game.createNpcType]
- `npcType.onThink` handler [chesa_the_guardian.lua:npcType.onThink]
- `npcType.onAppear` handler [chesa_the_guardian.lua:npcType.onAppear]
- `npcType.onDisappear` handler [chesa_the_guardian.lua:npcType.onDisappear]
- `npcType.onMove` handler [chesa_the_guardian.lua:npcType.onMove]
- `npcType.onSay` handler [chesa_the_guardian.lua:npcType.onSay]
- `npcType.onCloseChannel` handler [chesa_the_guardian.lua:npcType.onCloseChannel]
- `Game.createNpcType("Dahr-Enpa Rahng")` and `npcType:register(npcConfig)` [dahr-enpa_rahng.lua:Game.createNpcType]
- `npcType.onThink` handler [dahr-enpa_rahng.lua:npcType.onThink]
- `npcType.onAppear` handler [dahr-enpa_rahng.lua:npcType.onAppear]
- `npcType.onDisappear` handler [dahr-enpa_rahng.lua:npcType.onDisappear]
- `npcType.onMove` handler [dahr-enpa_rahng.lua:npcType.onMove]
- `npcType.onSay` handler [dahr-enpa_rahng.lua:npcType.onSay]
- `npcType.onCloseChannel` handler [dahr-enpa_rahng.lua:npcType.onCloseChannel]
- `creatureSayCallback(npc, creature, type, message)` dialogue callback [dahr-enpa_rahng.lua:creatureSayCallback]
- `Game.createNpcType("Dajcho The Monk")` and `npcType:register(npcConfig)` [dajcho_the_monk.lua:Game.createNpcType]
- `npcType.onThink` handler [dajcho_the_monk.lua:npcType.onThink]
- `npcType.onAppear` handler [dajcho_the_monk.lua:npcType.onAppear]

## Invariants
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [bodh_the_kan.lua:npcConfig.flags]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [chesa_the_guardian.lua:npcConfig.flags]
- `creatureSayCallback` requires active player focus verified by `npcHandler:checkInteraction(npc, creature)` [dahr-enpa_rahng.lua:creatureSayCallback]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [dahr-enpa_rahng.lua:npcConfig.flags]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [dajcho_the_monk.lua:npcConfig.flags]
- `creatureSayCallback` requires active player focus verified by `npcHandler:checkInteraction(npc, creature)` [enpa-deia_pema.lua:creatureSayCallback]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [enpa-deia_pema.lua:npcConfig.flags]
- `creatureSayCallback` requires active player focus verified by `npcHandler:checkInteraction(npc, creature)` [enpa_rudra.lua:creatureSayCallback]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [enpa_rudra.lua:npcConfig.flags]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [saih_the_guardian.lua:npcConfig.flags]

## Side Effects
- Registers NPC `Bodh The Kan` into the `Game` engine via `npcType:register(npcConfig)` [bodh_the_kan.lua:npcType:register]
- Registers NPC `Chesa The Guardian` into the `Game` engine via `npcType:register(npcConfig)` [chesa_the_guardian.lua:npcType:register]
- Registers NPC `Dahr-Enpa Rahng` into the `Game` engine via `npcType:register(npcConfig)` [dahr-enpa_rahng.lua:npcType:register]
- Registers NPC `Dajcho The Monk` into the `Game` engine via `npcType:register(npcConfig)` [dajcho_the_monk.lua:npcType:register]
- Registers NPC `Enpa-Deia Pema` into the `Game` engine via `npcType:register(npcConfig)` [enpa-deia_pema.lua:npcType:register]
- Processes item buy/sell transactions via `npc: buyItem`/`npc:sellItem` and `npcConfig.shop` [enpa-deia_pema.lua:npcConfig.shop]
- Registers NPC `Enpa Rudra` into the `Game` engine via `npcType:register(npcConfig)` [enpa_rudra.lua:npcType:register]
- Registers NPC `Saih The Guardian` into the `Game` engine via `npcType:register(npcConfig)` [saih_the_guardian.lua:npcType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
