# gamestore

## Overview
Package implementation for `data/libs/gamestore`, providing component logic and data interfaces for gamestore.

## Interface
- `helpers.convertType` (`[helpers.lua:helpers.convertType]`)
- `helpers.useOfferConfigure` (`[helpers.lua:helpers.useOfferConfigure]`)
- `orders.withPaidOrder` (`[orders.lua:orders.withPaidOrder]`): Reserves, claims, delivers, finishes, and records history for paid GameStore orders with pending-reconciliation safety.
- `taskboard.isWeeklyExpansionUnlocked`, `taskboard.unlockWeeklyExpansion` (`[taskboard.lua:taskboard.isWeeklyExpansionUnlocked]`, `[taskboard.lua:taskboard.unlockWeeklyExpansion]`): Bridges GameStore offers to `_G.Taskboard.expansion`.

## Invariants

- A purchase reserves a durable order and debits the selected coin balance in one transaction. The order must enter `delivering` before the server calls its fulfillment handler.
- The server confirms the purchase after saving the delivery and marking the order `complete`. An account can have one pending order. A retry reports the pending order without charging again or calling the handler again.

## Reconciling a pending order

1. As a god, run `/storeorder <id>` to inspect the order, its character, and its charge.
2. For a `delivering` order, verify the delivery for the recorded character and offer. An interrupted handler may have applied some of its changes. Check those changes before choosing an outcome.
3. For a verified delivery, run `/storeorder <id> complete verified`. If you verified that the delivery produced no lasting benefit or reversed the partial delivery, run `/storeorder <id> refund verified`. A `reserved` order can be refunded because fulfillment can only start after the next state transition.
4. If the command reports `uncertain`, inspect the order again before acting. The refund and the `refunded` transition commit together. Repeating a recorded refund returns its state without crediting again.

## Side Effects
- Executes SQL queries against game database (`[parsers.lua]`)
- Executes SQL queries against game database (`[store.lua]`)

## Verification
- See the [Lua regression guide](../../../tests/lua/README.md).
