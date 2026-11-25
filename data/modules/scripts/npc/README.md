# NPC Dialog Module (`data/modules/scripts/npc`)

## Overview
Maintains per-player open NPC dialog stacks (`NpcDialog`) and sends opcode `0x1C` dialog windows with context-sensitive action buttons (trade, sail, bank, hireling skills, yes/no/bye).

## Interface
- `NpcDialog.ValidProfessions` (`[npc_dialog.lua:NpcDialog.ValidProfessions]`): Supported NPC profession keys (`normal`, `sailor`, `banker`, `king`, `queen`, `trader`, `hireling`).
- `NpcDialog.add(player, npcId)`, `NpcDialog.remove(player, npcId)`, `NpcDialog.clear(player)` (`[npc_dialog.lua:NpcDialog.add]`): Manages deduplicated per-player active NPC ID lists in `NpcDialog._stateByPlayerId`.
- `NpcDialog.buildActions(player, npc)` (`[npc_dialog.lua:NpcDialog.buildActions]`): Builds action button entries (`Trade`, `TradePotion`, `TradeEquipment`, `Sail`, `DepositAll`, `Withdraw`, `Balance`, `Yes`, `No`, `Bye`) based on `npc:isMerchant()`, `NpcDialogProfessionByName`, and `hireling-skills` KV flags.
- `NpcDialog.sendWindow(player)` (`[npc_dialog.lua:NpcDialog.sendWindow]`): Serializes and transmits opcode `0x1C` with active NPC IDs and action buttons for the top NPC.

## Invariants
- `NpcDialog.add` and `NpcDialog.remove` ignore nil/zero `npcId` values and prevent duplicate `npcId` entries per player (`[npc_dialog.lua:NpcDialog.add]`).
- If the top `Npc(npcIds[#npcIds])` no longer exists when `sendWindow` runs, the player's dialog list is cleared and a close payload (`0x1C`, `0x01`) is sent (`[npc_dialog.lua:NpcDialog.sendWindow]`).

## Side Effects
- Mutates `NpcDialog._stateByPlayerId` and sends `NetworkMessage` (`0x1C`) packets to `player` (`[npc_dialog.lua:NpcDialog.sendWindow]`).

## Verification
- See the [Lua regression guide](../../../../tests/lua/README.md).
