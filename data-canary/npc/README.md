# Canary NPC Definitions (`data-canary/npc`)

## Overview
Defines and registers the `"Canary"` guide, shopkeeper, and promotion NPC (`canary.lua`) for the `data-canary` datapack.

## Interface
- `[canary.lua:npcType]` — `Game.createNpcType("Canary")` registered via `npcType:register(npcConfig)` (`[canary.lua:190]`).
- `[canary.lua:npcConfig]` — Configures NPC health (`100`), walk interval/radius (`2000`/`10`), outfit (`lookType = 128`, `lookMount = 42`), sound effects, voices, `floorchange = false`, and a 30-item `shop` table (`[canary.lua:46]`).
- Event callbacks: `[canary.lua:npcType.onThink]`, `[canary.lua:npcType.onAppear]`, `[canary.lua:npcType.onDisappear]`, `[canary.lua:npcType.onMove]`, `[canary.lua:npcType.onSay]`, `[canary.lua:npcType.onCloseChannel]`, `[canary.lua:npcType.onBuyItem]`, `[canary.lua:npcType.onSellItem]`, `[canary.lua:npcType.onCheckItem]`.
- Dialogue handlers: `[canary.lua:greetCallback]`, `[canary.lua:creatureSayCallback]` (topics `0` -> `1` for `"canary"` and `"discord group"`), and `"promot"` keyword node (`StdModule.promotePlayer`, `cost = 20000`, `level = 20`).

## Invariants
- `[canary.lua:132]` requires level `>= 20` and `20000` gold coins to promote a player via `StdModule.promotePlayer`.
- `[canary.lua:154]` requires `npcHandler:checkInteraction(npc, player)` to pass before processing `creatureSayCallback` dialogue topics.

## Side Effects
- `[canary.lua:190]` registers the `"Canary"` `NpcType` in the server engine.
- `[canary.lua:114]` and `[canary.lua:132]` mutate player inventory, gold balance, and vocation promotion state during shop transactions and promotions.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
