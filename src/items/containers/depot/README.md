# depot

## Overview
Provides specialized `Container` subclasses (`DepotChest` and `DepotLocker`) representing player depot storage chests and town locker containers. `DepotChest` enforces item holding limits (`maxDepotItems`) and ownership rules while delegating cylinder notifications up to the locker's parent, whereas `DepotLocker` holds the player's depot chest and inbox, serializes `ATTR_DEPOT_ID`, and prevents direct item additions into the locker slots.

## Interface
- `DepotChest` (`[depotchest.hpp:DepotChest]`): Paginated container (`maxSize = 32`, `maxDepotItems = 2000` by default) representing a numbered depot box (`[depotchest.cpp:DepotChest::DepotChest]`).
  - `setMaxDepotItems(uint32_t maxitems)` (`[depotchest.hpp:DepotChest::setMaxDepotItems]`)
  - `queryAdd(int32_t index, const std::shared_ptr<Thing> &thing, uint32_t count, uint32_t flags, const std::shared_ptr<Creature> &actor)` (`[depotchest.hpp:DepotChest::queryAdd]`, `[depotchest.cpp:DepotChest::queryAdd]`)
  - `postAddNotification(...)` / `postRemoveNotification(...)` (`[depotchest.hpp:DepotChest::postAddNotification]`, `[depotchest.hpp:DepotChest::postRemoveNotification]`)
  - `isDepotChest()`, `canRemove()`, `isRemoved()`, `getParent()`, `getRealParent()` (`[depotchest.hpp:DepotChest::isDepotChest]`, `[depotchest.hpp:DepotChest::canRemove]`, `[depotchest.hpp:DepotChest::isRemoved]`, `[depotchest.hpp:DepotChest::getParent]`, `[depotchest.hpp:DepotChest::getRealParent]`)
- `DepotLocker` (`[depotlocker.hpp:DepotLocker]`): Town depot locker container storing a `depotId` and child containers (`[depotlocker.cpp:DepotLocker::DepotLocker]`).
  - `getDepotLocker()` (`[depotlocker.hpp:DepotLocker::getDepotLocker]`)
  - `removeInbox(const std::shared_ptr<Inbox> &inbox)` (`[depotlocker.hpp:DepotLocker::removeInbox]`, `[depotlocker.cpp:DepotLocker::removeInbox]`)
  - `readAttr(AttrTypes_t attr, PropStream &propStream)` (`[depotlocker.hpp:DepotLocker::readAttr]`, `[depotlocker.cpp:DepotLocker::readAttr]`)
  - `getDepotId()` / `setDepotId(uint16_t newDepotId)` (`[depotlocker.hpp:DepotLocker::getDepotId]`, `[depotlocker.hpp:DepotLocker::setDepotId]`)
  - `queryAdd(...)`, `postAddNotification(...)`, `postRemoveNotification(...)`, `canRemove()`, `isRemoved()` (`[depotlocker.hpp:DepotLocker::queryAdd]`, `[depotlocker.hpp:DepotLocker::postAddNotification]`, `[depotlocker.hpp:DepotLocker::postRemoveNotification]`, `[depotlocker.hpp:DepotLocker::canRemove]`, `[depotlocker.hpp:DepotLocker::isRemoved]`)

## Invariants
- Both `DepotChest` and `DepotLocker` are non-removable and never flagged as removed (`canRemove() == false`, `isRemoved() == false`) (`[depotchest.hpp:DepotChest::canRemove]`, `[depotchest.hpp:DepotChest::isRemoved]`, `[depotlocker.hpp:DepotLocker::canRemove]`, `[depotlocker.hpp:DepotLocker::isRemoved]`).
- `DepotLocker::queryAdd` unconditionally returns `RETURNVALUE_NOTENOUGHROOM`, preventing items from being placed directly inside the locker outside of its child containers (`[depotlocker.cpp:DepotLocker::queryAdd]`).
- `DepotChest::queryAdd` rejects items owned by another creature (`RETURNVALUE_ITEMISNOTYOURS`) and, unless `FLAG_NOLIMIT` is set, enforces `maxDepotItems` across the real parent's container holding count or its own holding count (`RETURNVALUE_DEPOTISFULL`) (`[depotchest.cpp:DepotChest::queryAdd]`).
- `DepotChest::getParent` traverses three parent levels (`m_parent.lock()->getParent()->getParent()`) while `getRealParent` returns `m_parent.lock()` (`[depotchest.cpp:DepotChest::getParent]`, `[depotchest.hpp:DepotChest::getRealParent]`).

## Side Effects
- `DepotChest::postAddNotification` and `DepotChest::postRemoveNotification` forward cylinder notifications to `getParent()` with `LINK_PARENT` (`[depotchest.cpp:DepotChest::postAddNotification]`, `[depotchest.cpp:DepotChest::postRemoveNotification]`).
- `DepotLocker::postAddNotification` and `DepotLocker::postRemoveNotification` forward cylinder notifications to `m_parent.lock()` with `LINK_PARENT` (`[depotlocker.cpp:DepotLocker::postAddNotification]`, `[depotlocker.cpp:DepotLocker::postRemoveNotification]`).
- `DepotLocker::readAttr` reads `ATTR_DEPOT_ID` from `PropStream` and mutates `depotId` (`[depotlocker.cpp:DepotLocker::readAttr]`).
- `DepotLocker::removeInbox` erases the matching `Inbox` from `itemlist` (`[depotlocker.cpp:DepotLocker::removeInbox]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
