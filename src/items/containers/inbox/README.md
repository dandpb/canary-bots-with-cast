# inbox

## Overview
Implements the `Inbox` container (`[inbox.hpp:Inbox]`), a paginated, locked (`unlocked = false`, `pagination = true`, `maxSize = 30`) player mail and parcel inbox container that restricts direct player item insertion while allowing system mail/parcel delivery up to `MAX_INBOX_ITEMS`.

## Interface
- `Inbox` (`[inbox.hpp:Inbox]`): Final `Container` subclass for player mail/inbox items (`[inbox.cpp:Inbox::Inbox]`).
  - `setMaxInboxItems(uint32_t maxitems)` (`[inbox.hpp:Inbox::setMaxInboxItems]`)
  - `queryAdd(int32_t index, const std::shared_ptr<Thing> &thing, uint32_t count, uint32_t flags, const std::shared_ptr<Creature> &actor)` (`[inbox.hpp:Inbox::queryAdd]`, `[inbox.cpp:Inbox::queryAdd]`)
  - `postAddNotification(...)` / `postRemoveNotification(...)` (`[inbox.hpp:Inbox::postAddNotification]`, `[inbox.hpp:Inbox::postRemoveNotification]`)
  - `isInbox()`, `canRemove()`, `isRemoved()`, `getParent()`, `getRealParent()` (`[inbox.hpp:Inbox::isInbox]`, `[inbox.hpp:Inbox::canRemove]`, `[inbox.hpp:Inbox::isRemoved]`, `[inbox.hpp:Inbox::getParent]`, `[inbox.hpp:Inbox::getRealParent]`)

## Invariants
- `Inbox` is non-removable and never marked removed (`canRemove() == false`, `isRemoved() == false`, `isInbox() == true`) (`[inbox.hpp:Inbox::canRemove]`, `[inbox.hpp:Inbox::isRemoved]`, `[inbox.hpp:Inbox::isInbox]`).
- `Inbox::queryAdd` requires `FLAG_NOLIMIT` in `flags` (otherwise returning `RETURNVALUE_CONTAINERNOTENOUGHROOM`), requires a valid pickupable `Item` (`RETURNVALUE_NOTPOSSIBLE` / `RETURNVALUE_CANNOTPICKUP`), forbids self-insertion (`RETURNVALUE_THISISIMPOSSIBLE`), and enforces `getItemHoldingCount() + addCount <= maxInboxItems` (`RETURNVALUE_DEPOTISFULL`) (`[inbox.cpp:Inbox::queryAdd]`).
- `Inbox::getParent` returns `m_parent.lock()->getParent()` (skipping the enclosing `DepotLocker` to reach the player), while `getRealParent` returns `m_parent.lock()` (`[inbox.cpp:Inbox::getParent]`, `[inbox.hpp:Inbox::getRealParent]`).

## Side Effects
- Constructor reads `MAX_INBOX_ITEMS` from `g_configManager()` (`[inbox.cpp:Inbox::Inbox]`).
- `Inbox::postAddNotification` and `Inbox::postRemoveNotification` propagate notifications to `getParent()` with `LINK_PARENT` (`[inbox.cpp:Inbox::postAddNotification]`, `[inbox.cpp:Inbox::postRemoveNotification]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
