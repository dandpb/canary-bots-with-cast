# rewards

## Overview
Implements boss reward containers: `Reward` (`ITEM_REWARD_CONTAINER`, representing an individual boss reward bag) and `RewardChest` (representing the town/boss reward chest that holds `Reward` containers). Both are locked (`unlocked = false`), paginated (`pagination = true`, `maxSize = 32`) `Container` subclasses that disallow player-initiated item insertions (`actor != nullptr`).

## Interface
- `Reward` (`[reward.hpp:Reward]`): Final `Container` subclass initialized with `ITEM_REWARD_CONTAINER` (`[reward.cpp:Reward::Reward]`).
  - `getReward()` (`[reward.hpp:Reward::getReward]`)
  - `queryAdd(int32_t index, const std::shared_ptr<Thing> &thing, uint32_t count, uint32_t flags, const std::shared_ptr<Creature> &actor)` (`[reward.hpp:Reward::queryAdd]`, `[reward.cpp:Reward::queryAdd]`)
  - `postAddNotification(...)` / `postRemoveNotification(...)` (`[reward.hpp:Reward::postAddNotification]`, `[reward.hpp:Reward::postRemoveNotification]`)
  - `canRemove()`, `getParent()`, `getRealParent()` (`[reward.hpp:Reward::canRemove]`, `[reward.hpp:Reward::getParent]`, `[reward.hpp:Reward::getRealParent]`)
- `RewardChest` (`[rewardchest.hpp:RewardChest]`): Final `Container` subclass representing a reward chest (`[rewardchest.cpp:RewardChest::RewardChest]`).
  - `getRewardChest()` (`[rewardchest.hpp:RewardChest::getRewardChest]`)
  - `queryAdd(int32_t index, const std::shared_ptr<Thing> &thing, uint32_t count, uint32_t flags, const std::shared_ptr<Creature> &actor)` (`[rewardchest.hpp:RewardChest::queryAdd]`, `[rewardchest.cpp:RewardChest::queryAdd]`)
  - `postAddNotification(...)` / `postRemoveNotification(...)` (`[rewardchest.hpp:RewardChest::postAddNotification]`, `[rewardchest.hpp:RewardChest::postRemoveNotification]`)
  - `canRemove()` (`[rewardchest.hpp:RewardChest::canRemove]`)
  - `removeItem(const std::shared_ptr<Thing> &thing, bool sendToClient = false)` (`[rewardchest.hpp:RewardChest::removeItem]`, `[rewardchest.cpp:RewardChest::removeItem]`)

## Invariants
- Both `Reward` and `RewardChest` initialize with `maxSize = 32`, `unlocked = false`, and `pagination = true` (`[reward.cpp:Reward::Reward]`, `[rewardchest.cpp:RewardChest::RewardChest]`).
- `Reward::queryAdd` and `RewardChest::queryAdd` reject any addition when `actor != nullptr` (`RETURNVALUE_NOTPOSSIBLE`), preventing players from placing items into reward containers (`[reward.cpp:Reward::queryAdd]`, `[rewardchest.cpp:RewardChest::queryAdd]`).
- `Reward::queryAdd` additionally requires a valid pickupable `Item` and forbids self-addition (`RETURNVALUE_THISISIMPOSSIBLE`, `RETURNVALUE_CANNOTPICKUP`) (`[reward.cpp:Reward::queryAdd]`).
- `Reward::canRemove()` returns `true` (`[reward.hpp:Reward::canRemove]`), whereas `RewardChest::canRemove()` returns `false` (`[rewardchest.hpp:RewardChest::canRemove]`).

## Side Effects
- `Reward::postAddNotification` / `postRemoveNotification` and `RewardChest::postAddNotification` / `postRemoveNotification` forward cylinder notifications to their parent cylinder with `LINK_PARENT` (`[reward.cpp:Reward::postAddNotification]`, `[reward.cpp:Reward::postRemoveNotification]`, `[rewardchest.cpp:RewardChest::postAddNotification]`, `[rewardchest.cpp:RewardChest::postRemoveNotification]`).
- `RewardChest::removeItem` erases the target item from `itemlist` and calls `itemToRemove->resetParent()` without sending client container updates (`[rewardchest.cpp:RewardChest::removeItem]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
