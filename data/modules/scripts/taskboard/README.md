# Taskboard Module (`data/modules/scripts/taskboard`)

## Overview
Implements the Bounty Taskboard, Weekly Taskboard, Talisman/Shop, and Soulpit integration module (`Taskboard`) loaded by Canary's module system and exposed globally for talkactions, event callbacks, and player lifecycle hooks.

## Interface
- `Taskboard` entrypoint and `onRecvbyte(player, msg, byte)` (`[taskboard.lua:onRecvbyte]`): Bootstraps subcomponents in order (`settings`, `diagnostics`, `catalog`, `state`, `rules`, `wire`, `expansion`, `admin`, `actions`, `soulpit`, `lifecycle`), exports top-level helpers (`getLootBonus`, `getCombatBonuses`, `getDamageBonus`, `getLifeLeechBonus`, `onMonsterKilled`, `openSoulpitWindow`), and routes client opcodes `0x5F` (`clientTaskboard`) and `0xBA` (`clientSoulpit`).
- `settings.lua`: Defines protocol opcodes (`0x5F`, `0x5B`, `0xBA`, `0xEE`, `0x75`), window IDs (`bounty`, `weekly`, `shop`), client actions, and difficulty/config tables (`[settings.lua:api.packet]`).
- `diagnostics.lua`: Tracing, client version inspection, and byte-formatting helpers (`[diagnostics.lua]`).
- `catalog.lua`: Rebuilds monster race (`byRaceId`) and weekly delivery item catalogs (`catalog.rebuild`) from `Game.getMonsterTypes()` (`[catalog.lua:catalog.rebuild]`).
- `state.lua`: Reads, initializes, and normalizes per-player taskboard KV/storage state (`api.state.ensure`) (`[state.lua]`).
- `rules.lua`: Computes bounty/weekly difficulty rules, combat/loot/life-leech bonuses, kill progress, and creature icon synchronization (`pendingFinalLootBonuses`) (`[rules.lua]`).
- `wire.lua`: Serializes and sends taskboard balances (`0xEE`), bounty, weekly, and shop payloads (`0x5B`) for clients supporting the protocol (`[wire.lua:wire.sendBalances]`).
- `expansion.lua`: Manages weekly expansion unlock state (`expansion.isUnlocked`, `expansion.setUnlocked`) (`[expansion.lua:expansion.isUnlocked]`).
- `admin.lua`: GM/administrative state adjustments and balance/weekly synchronization (`[admin.lua]`).
- `actions.lua`: Parses and dispatches client taskboard actions (`openBounty`..`assignUnwanted`) (`[actions.lua]`).
- `soulpit.lua`: Manages Soulpit window opening, session-scoped authorizations, and client selection handling (`[soulpit.lua]`).
- `lifecycle.lua`: Registers `TaskboardLogin` (`CreatureEvent`) and login/lifecycle synchronization (`[lifecycle.lua]`).

## Invariants
- Module initialization guards against duplicate bootstrapping using `Taskboard.__entrypoint == taskboardPath` (`[taskboard.lua]`).
- `onRecvbyte` ignores incoming taskboard/soulpit packets whenever `Taskboard.isEnabled()` is false (`[taskboard.lua:onRecvbyte]`).
- `rules.lua` captures `pendingFinalLootBonuses` keyed by player and monster IDs because kill progress completes before corpse loot generation (`[rules.lua]`).

## Side Effects
- Exposes global `_G.Taskboard`, registers `CreatureEvent("TaskboardLogin")`, mutates player scoped KV/storage state, and sends `NetworkMessage` packets (`0x5B`, `0xBA`, `0xEE`, `0x75`) to players (`[taskboard.lua]`, `[wire.lua]`, `[lifecycle.lua]`).

## Verification
- See the [Lua regression guide](../../../../tests/lua/README.md).
