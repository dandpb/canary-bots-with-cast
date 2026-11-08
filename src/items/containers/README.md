# containers

## Overview
Provides the core `Container` class (`[container.hpp:Container]`)—an `Item` and `Cylinder` implementation that holds an ordered `ItemDeque` of child items, tracks recursive item weight, supports browse-field virtual containers, store inbox filtering, loot highlight management, and cycle-safe depth-bounded recursive iteration via `ContainerIterator` (`[container.hpp:ContainerIterator]`)—along with specialized container subdirectories (`depot`, `inbox`, `mailbox`, `rewards`).

## Interface
- `ContainerIterator` (`[container.hpp:ContainerIterator]`): Depth-bounded, cycle-detecting iterator over nested containers (`[container.cpp:ContainerIterator::ContainerIterator]`, `[container.hpp:ContainerIterator::hasNext]`, `[container.hpp:ContainerIterator::advance]`, `[container.hpp:ContainerIterator::operator*]`, `[container.hpp:ContainerIterator::hasReachedMaxDepth]`, `[container.hpp:ContainerIterator::getCurrentContainer]`, `[container.hpp:ContainerIterator::getCurrentIndex]`).
- `Container` (`[container.hpp:Container]`): Base container item and cylinder (`[container.cpp:Container::Container]`).
  - Factory & lifecycle: `create(...)`, `createBrowseField(const std::shared_ptr<Tile> &tile)`, `clone()` (`[container.hpp:Container::create]`, `[container.hpp:Container::createBrowseField]`, `[container.hpp:Container::clone]`).
  - Hierarchy & type queries: `getContainer()`, `getCylinder()`, `getRootContainer()`, `getDepotLocker()`, `getRewardChest()`, `getReward()`, `isInbox()`, `isDepotChest()`, `isStoreInbox()`, `isStoreInboxFiltered()`, `isAnyKindOfRewardChest()`, `isAnyKindOfRewardContainer()`, `isBrowseFieldAndHoldsRewardChest()`, `isBrowsefield()`, `isUnlocked()`, `hasPagination()`, `hasParent()`, `countsToLootAnalyzerBalance()` (`[container.hpp:Container::getContainer]`, `[container.hpp:Container::getRootContainer]`, `[container.hpp:Container::isStoreInbox]`, `[container.hpp:Container::isBrowsefield]`).
  - Content & capacity inspection: `size()`, `empty()`, `capacity()`, `getMaxCapacity()`, `iterator()`, `getItemList()`, `getReversedItems()`, `getReversedEnd()`, `getItems(bool recursive)`, `getItemByIndex(size_t index)`, `getFilteredItemByIndex(size_t index)`, `getStoreInboxFilteredItems()`, `getStoreInboxValidCategories()`, `getStowableItems()`, `isHoldingItem(...)`, `isHoldingItemWithId(uint16_t id)`, `isInsideContainerWithId(uint16_t id)`, `getItemHoldingCount()`, `getContainerHoldingCount()`, `getFreeSlots()`, `getWeight()`, `getOwnerId()`, `getContentDescription(bool sendColoredMessage)`, `getSpecialCategory(...)`, `getObjectCategoryFlags(...)`, `getAmmoAmount(...)`, `clearLootHighlight(...)`, `hasLootHighlight()` (`[container.hpp:Container::size]`, `[container.hpp:Container::getItemHoldingCount]`, `[container.hpp:Container::getWeight]`, `[container.hpp:Container::getSpecialCategory]`).
  - Serialization: `readAttr(AttrTypes_t attr, PropStream &propStream)`, `unserializeItemNode(...)` (`[container.hpp:Container::readAttr]`, `[container.hpp:Container::unserializeItemNode]`).
  - Cylinder operations: `queryAdd(...)`, `queryMaxCount(...)`, `queryRemove(...)`, `queryDestination(...)`, `addThing(...)`, `addItem(const std::shared_ptr<Item> &item)`, `addItemBack(const std::shared_ptr<Item> &item)`, `updateThing(...)`, `replaceThing(...)`, `removeThing(...)`, `removeItem(...)`, `internalAddThing(...)`, `getThingIndex(...)`, `getFirstIndex()`, `getLastIndex()`, `getItemTypeCount(...)`, `getAllItemTypeCount(...)`, `getThing(size_t index)`, `postAddNotification(...)`, `postRemoveNotification(...)` (`[container.hpp:Container::queryAdd]`, `[container.hpp:Container::addThing]`, `[container.hpp:Container::removeThing]`).
- Subdirectories:
  - [depot](./depot/README.md): Player depot chest (`DepotChest`) and town depot locker (`DepotLocker`) containers.
  - [inbox](./inbox/README.md): Player mail/parcel `Inbox` container with `MAX_INBOX_ITEMS` capacity enforcement.
  - [mailbox](./mailbox/README.md): In-world `Mailbox` item and cylinder that routes letters and parcels into recipient inboxes.
  - [rewards](./rewards/README.md): Boss `Reward` bag and `RewardChest` containers.

## Invariants
- `ContainerIterator` never traverses deeper than `maxTraversalDepth` (`MAX_CONTAINER_DEPTH`) and tracks `visitedContainers` to prevent infinite loops on cyclic container references (`[container.cpp:ContainerIterator::advance]`).
- `Container::queryAdd` rejects additions when `!unlocked`, when the item is not pickupable, when adding a container to itself or an ancestor cylinder (`cylinder == addThing`), when `cylinder == parent` (cycle guard), when item ownership conflicts (`RETURNVALUE_ITEMISNOTYOURS`), when non-ammo is added to a quiver (`RETURNVALUE_ONLYAMMOINQUIVER`), or when container/item count limits (`MAX_CONTAINER`, `m_maxItems`, `capacity()`) are exceeded without `FLAG_NOLIMIT` (`[container.cpp:Container::queryAdd]`).
- `Container::getWeight()` always equals `Item::getWeight() + totalWeight`, and `updateItemWeight(int32_t diff)` propagates weight deltas up all ancestor containers (`[container.cpp:Container::getWeight]`, `[container.cpp:Container::updateItemWeight]`).
- Child invariants from `depot`, `inbox`, `mailbox`, and `rewards` apply to their respective subclasses (`[depotchest.cpp:DepotChest::queryAdd]`, `[inbox.cpp:Inbox::queryAdd]`, `[mailbox.cpp:Mailbox::canSend]`, `[reward.cpp:Reward::queryAdd]`).

## Side Effects
- `Container::~Container` removes `ITEM_BROWSEFIELD` entries from `g_game().browseFields` and restores parent pointers of browsed items back to the tile (`[container.cpp:Container::~Container]`).
- Mutating cylinder methods (`addThing`, `addItemBack`, `updateThing`, `replaceThing`, `removeThing`, `removeItem`, `clearLootHighlight`) mutate `itemlist` and `totalWeight`, update item parent pointers, and notify holding players or nearby `Spectators` via `sendAddContainerItem` / `sendUpdateContainerItem` / `sendRemoveContainerItem` and player container event callbacks (`[container.cpp:Container::onAddContainerItem]`, `[container.cpp:Container::onUpdateContainerItem]`, `[container.cpp:Container::onRemoveContainerItem]`).
- `Container::unserializeItemNode` instantiates child items via `Item::CreateItem` from OTBM nodes (`[container.cpp:Container::unserializeItemNode]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
