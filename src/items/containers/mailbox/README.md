# mailbox

## Overview
Implements the `Mailbox` item and cylinder (`[mailbox.hpp:Mailbox]`), which acts as an in-world drop target for letters (`ITEM_LETTER`) and parcels (`ITEM_PARCEL`). When a valid mailable item is added to the `Mailbox`, it parses the recipient player name from the letter's text or parcel's `ITEM_LABEL`, moves the item into the recipient's `Inbox`, transforms the item (e.g., stamping letters into `ITEM_LETTER_STAMPED`), and either notifies the online recipient or persists the offline recipient via `SaveManager`.

## Interface
- `Mailbox` (`[mailbox.hpp:Mailbox]`): Final class inheriting from `Item` and `Cylinder`.
  - `Mailbox(uint16_t itemId)` (`[mailbox.hpp:Mailbox::Mailbox]`)
  - `getMailbox()` / `getCylinder()` (`[mailbox.hpp:Mailbox::getMailbox]`, `[mailbox.hpp:Mailbox::getCylinder]`)
  - `queryAdd(...)`, `queryMaxCount(...)`, `queryRemove(...)`, `queryDestination(...)` (`[mailbox.hpp:Mailbox::queryAdd]`, `[mailbox.hpp:Mailbox::queryMaxCount]`, `[mailbox.hpp:Mailbox::queryRemove]`, `[mailbox.hpp:Mailbox::queryDestination]`)
  - `addThing(const std::shared_ptr<Thing> &thing)` / `addThing(int32_t index, const std::shared_ptr<Thing> &thing)` (`[mailbox.hpp:Mailbox::addThing]`, `[mailbox.cpp:Mailbox::addThing]`)
  - `updateThing(...)`, `replaceThing(...)`, `removeThing(...)` (`[mailbox.hpp:Mailbox::updateThing]`, `[mailbox.hpp:Mailbox::replaceThing]`, `[mailbox.hpp:Mailbox::removeThing]`)
  - `postAddNotification(...)` / `postRemoveNotification(...)` (`[mailbox.hpp:Mailbox::postAddNotification]`, `[mailbox.hpp:Mailbox::postRemoveNotification]`)

## Invariants
- `Mailbox::canSend` only permits items that have no owner (`!item->hasOwner()`) and whose ID is `ITEM_PARCEL` or `ITEM_LETTER` (`[mailbox.cpp:Mailbox::canSend]`).
- `Mailbox::queryAdd` returns `RETURNVALUE_NOERROR` only when `thing->getItem()` satisfies `Mailbox::canSend`, and `RETURNVALUE_NOTPOSSIBLE` otherwise (`[mailbox.cpp:Mailbox::queryAdd]`).
- `Mailbox::queryRemove` always returns `RETURNVALUE_NOTPOSSIBLE`, and `updateThing`, `replaceThing`, and `removeThing` are no-ops (`[mailbox.cpp:Mailbox::queryRemove]`, `[mailbox.cpp:Mailbox::updateThing]`, `[mailbox.cpp:Mailbox::replaceThing]`, `[mailbox.cpp:Mailbox::removeThing]`).

## Side Effects
- `Mailbox::sendItem` (invoked by `Mailbox::addThing`) auto-closes open containers on nearby `Spectators` if the mailed item is a container on a tile (`[mailbox.cpp:Mailbox::sendItem]`).
- `Mailbox::sendItem` looks up or loads the recipient player via `g_game().getPlayerByName(receiver, true)`, moves the item into `player->getInbox()` via `g_game().internalMoveItem(..., FLAG_NOLIMIT)`, transforms the item to `item->getID() + 1` via `g_game().transformItem` (preserving `WRITER`, `DATE`, and `TEXT` attributes on `ITEM_LETTER_STAMPED`), and calls `player->onReceiveMail()` if online or `g_saveManager().savePlayer(player)` if offline (`[mailbox.cpp:Mailbox::sendItem]`).
- `Mailbox::postAddNotification` and `Mailbox::postRemoveNotification` forward notifications to `getParent()` with `LINK_PARENT` (`[mailbox.cpp:Mailbox::postAddNotification]`, `[mailbox.cpp:Mailbox::postRemoveNotification]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
