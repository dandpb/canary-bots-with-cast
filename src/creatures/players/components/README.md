# Player Components

## Overview
Gathers modular per-player components (`PlayerAchievement`, `PlayerAttachedEffects`, `PlayerBadge`, `PlayerCyclopedia`, `PlayerForgeHistory`, `PlayerStorage`, `PlayerTitle`, `PlayerVIP`, and the `./wheel` subsystem) that decouple specific feature domains from the core `Player` entity, improving maintainability, readability, and testability.

## Interface
- `PlayerAchievement`, `Achievement` (`[player_achievement.hpp:PlayerAchievement]`, `[player_achievement.hpp:Achievement]`, `[player_achievement.cpp:PlayerAchievement]`): Manages unlocked player achievements and points (`add`, `remove`, `isUnlocked`, `getPoints`, `addPoints`, `removePoints`, `loadUnlockedAchievements`, `sendUnlockedSecretAchievements`).
- `PlayerAttachedEffects` (`[player_attached_effects.hpp:PlayerAttachedEffects]`, `[player_attached_effects.cpp:PlayerAttachedEffects]`): Manages cosmetic wings, auras, effects, and shaders (`toggleWing`, `tameWing`, `untameWing`, `toggleAura`, `tameAura`, `untameAura`, `toggleEffect`, `tameEffect`, `untameEffect`, `toggleShader`, `tameShader`, `untameShader`, `addCustomOutfit`, `removeCustomOutfit`, `sendAttachedEffect`, `sendDetachEffect`, `sendShader`, `sendMapShader`).
- `PlayerBadge`, `Badge` (`[player_badge.hpp:PlayerBadge]`, `[player_badge.hpp:Badge]`, `[player_badge.cpp:PlayerBadge]`): Evaluates and unlocks account/character Cyclopedia badges (`hasBadge`, `add`, `checkAndUpdateNewBadges`, `loadUnlockedBadges`).
- `PlayerCyclopedia`, `Summary` (`[player_cyclopedia.hpp:PlayerCyclopedia]`, `[player_cyclopedia.hpp:Summary]`, `[player_cyclopedia.cpp:PlayerCyclopedia]`): Manages Cyclopedia character summaries, asynchronous recent death and PvP kill queries, and store summary counters (`getSummary`, `loadSummaryData`, `loadDeathHistory`, `loadRecentKills`, `updateStoreSummary`, `getAmount`, `updateAmount`).
- `PlayerForgeHistory`, `ForgeHistory`, `PlayerForgeHistory::Pending` (`[player_forge_history.hpp:PlayerForgeHistory]`, `[player_forge_history.hpp:ForgeHistory]`, `[player_forge_history.cpp:PlayerForgeHistory]`): Tracks and persists Exaltation Forge action history with delta tracking (`get`, `add`, `remove`, `load`, `save`, `pending`, `acknowledge`).
- `PlayerStorage`, `PlayerStorageRow`, `PlayerStorage::PlayerStorageDelta` (`[player_storage.hpp:PlayerStorage]`, `[player_storage.hpp:PlayerStorageRow]`, `[player_storage.cpp:PlayerStorage]`): Thread-safe key-value storage manager with dirty/deleted delta tracking and reserved range expansion (`ingest`, `add`, `remove`, `has`, `get`, `prepareForPersist`, `delta`, `clearDirty`, `acknowledge`).
- `PlayerTitle`, `Title` (`[player_title.hpp:PlayerTitle]`, `[player_title.hpp:Title]`, `[player_title.cpp:PlayerTitle]`): Evaluates, unlocks, and selects character titles (`isTitleUnlocked`, `manage`, `remove`, `getUnlockedTitles`, `getCurrentTitle`, `setCurrentTitle`, `getCurrentTitleName`, `checkAndUpdateNewTitles`, `loadUnlockedTitles`).
- `PlayerVIP`, `VIPGroup` (`[player_vip.hpp:PlayerVIP]`, `[player_vip.hpp:VIPGroup]`, `[player_vip.cpp:PlayerVIP]`): Manages VIP buddy entries and custom VIP groups (`add`, `addInternal`, `remove`, `edit`, `notifyStatusChange`, `addGroup`, `editGroup`, `removeGroup`, `getMaxEntries`, `getMaxGroupEntries`).
- [wheel](./wheel/README.md): Implements the Wheel of Destiny progression system, gem Atelier, and modifier strategies (`PlayerWheel`, `PlayerWheelGem`, `WheelModifierContext`).

## Invariants
- `PlayerStorage` protects all reads and mutations of `m_storageMap`, `m_modifiedKeys`, and `m_removedKeys` with `std::recursive_mutex mutex_` (`[player_storage.hpp:PlayerStorage::mutex_]`); assigning `-1` to a key removes it and records the key in `m_removedKeys` (`[player_storage.cpp:PlayerStorage::add]`).
- Reserved storage ranges for outfits (`PSTRG_OUTFITS_RANGE_START`) and familiars (`PSTRG_FAMILIARS_RANGE_START`) are unpacked into `m_player.outfits` and `m_player.familiars` on `add()` and re-encoded into `m_storageMap` only when `prepareForPersist()` is called (`[player_storage.cpp:PlayerStorage::add]`, `[player_storage.cpp:PlayerStorage::getReservedRange]`).
- `PlayerForgeHistory::add` monotonically increments `adjustedHistory.createdAt` if an entry with the same timestamp already exists in `m_history`, ensuring `(player_id, done_at)` uniqueness for statement-capturing checkpoints (`[player_forge_history.cpp:PlayerForgeHistory::add]`, `[player_forge_history.cpp:PlayerForgeHistory::save]`).
- `PlayerVIP` caps buddy entries at `group->maxVipEntries` (or 100 for premium, 20 for free, hard maximum 200) and custom VIP group IDs within `firstID`..`lastID` (`1`..`8`) (`[player_vip.cpp:PlayerVIP::getMaxEntries]`, `[player_vip.cpp:PlayerVIP::add]`, `[player_vip.cpp:PlayerVIP::getFreeId]`).
- Toggling wings, auras, effects, or shaders enforces a 3000ms exhaustion cooldown (`lastToggle*`) and is rejected while the player has `CONDITION_OUTFIT` active (`[player_attached_effects.cpp:PlayerAttachedEffects::toggleWing]`, `[player_attached_effects.cpp:PlayerAttachedEffects::toggleAura]`, `[player_attached_effects.cpp:PlayerAttachedEffects::toggleEffect]`, `[player_attached_effects.cpp:PlayerAttachedEffects::toggleShader]`).

## Side Effects
- Reads and writes scoped player `KV` entries for achievements, badges, titles, cyclopedia summaries, and last-used wings/auras/effects (`[player_achievement.cpp:PlayerAchievement::add]`, `[player_badge.cpp:PlayerBadge::add]`, `[player_title.cpp:PlayerTitle::manage]`, `[player_cyclopedia.cpp:PlayerCyclopedia::updateAmount]`, `[player_attached_effects.cpp:PlayerAttachedEffects::toggleWing]`).
- Executes synchronous and asynchronous SQL queries against `players`, `player_hirelings`, `player_deaths`, `forge_history`, `player_charms`, and VIP tables (`IOLoginData`) (`[player_badge.cpp:PlayerBadge::getPlayersInfoByAccount]`, `[player_cyclopedia.cpp:PlayerCyclopedia::loadDeathHistory]`, `[player_cyclopedia.cpp:PlayerCyclopedia::loadRecentKills]`, `[player_forge_history.cpp:PlayerForgeHistory::save]`, `[player_title.cpp:PlayerTitle::checkHighscore]`, `[player_vip.cpp:PlayerVIP::add]`).
- Fires Lua events and callbacks (`eventOnStorageUpdate`, `EventCallback_t::playerOnStorageUpdate`) when non-login storage keys change (`[player_storage.cpp:PlayerStorage::add]`) and sends network packets to the owning player's client (`ProtocolGame`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`

---

## PlayerStorage

`PlayerStorage` centralizes the management of a player's storages.
Previously, the storage map was directly managed by `Player`, which made the codebase more difficult to maintain and test. 
By encapsulating it, several benefits are gained:

### Key Improvements

- **Unified interface**: all read, write, and remove operations are exposed through a single API, avoiding direct manipulation of raw maps.
- **Performance optimization**:
  - Only **modified keys** are tracked and persisted to the database.
  - This avoids rewriting the entire storage map each save cycle.
  - The larger the storage set, the bigger the performance gains, especially on characters with thousands of storages.
- **Support for reserved ranges**:
  Special ranges are reserved for features like **outfits**, **familiars**, **mounts**, **auras**, and more.
  These are automatically expanded or serialized by the component.
- **Improved readability in reserved ranges**:
  Previously, some ranges (like mounts, wings, effects) were represented by empty `if` blocks that did nothing.
  These were confusing and gave the impression of incomplete code.
  The ranges were refactored into a **pass-through list**: a clear, explicit collection of ranges that are persisted normally without warnings.
  This makes the intent much clearer to future maintainers.
- **Event integration**:
  When storages are updated, the system automatically triggers events and callbacks (`eventOnStorageUpdate`, `playerOnStorageUpdate`).
  Scripts and subsystems can react instantly without requiring manual value checks. 
- **Consistency**:
  Database writes happen in controlled, batched queries (DELETE + UPSERT). This reduces the query count and maintains data consistency. 

---

### Usage Examples

#### Basic set and get
```cpp
// Assign a value to a storage
player.storage().add(1000, 1);

// Read the value
int value = player.storage().get(1000);
if (value != -1) {
	g_logger().info("Storage 1000 = {}", value);
}

```

#### Removal
```cpp
if (player.storage().remove(1000)) {
	g_logger().info("Key 1000 removed successfully");
}
```

#### Existence check
```cpp
if (player.storage().has(2000)) {
	g_logger().info("Tutorial step storage exists");
}
```

#### Persisting and loading
```cpp
// Save only modified/removed keys
if (!player.storage().save()) {
	g_logger().error("Failed to persist storages for player {}", player.getName());
}

// Reload everything on login
player.storage().load();
```

---

### Reserved Ranges

Certain storages are grouped into ranges that represent special systems.
For example:

```cpp
// Outfit storage: encoded as << 16 | addons
player.storage().add(PSTRG_OUTFITS_RANGE_START + 1, << 16 | addons);

// Familiar storage: encoded as << 16
player.storage().add(PSTRG_FAMILIARS_RANGE_START + 1, familiarLookType, 16);
```

#### Refactored Pass-Through Ranges

Mounts, wings, effects, auras, and shaders are defined as **pass-through ranges**.
This means:
- They belong to the reserved space.
- They are persisted like regular keys. 
- They no longer generate warnings or confusing empty blocks.

Implementation detail:
```cpp
static constexpr std::array<std::pair<uint32_t, uint32_t>, 5> passThroughRanges {{
	{PSTRG_MOUNTS_RANGE_START, PSTRG_MOUNTS_RANGE_SIZE},
	{PSTRG_WING_RANGE_START, PSTRG_WING_RANGE_SIZE},
	{PSTRG_EFFECT_RANGE_START, PSTRG_EFFECT_RANGE_SIZE},
	{PSTRG_AURA_RANGE_START, PSTRG_AURA_RANGE_SIZE},
	{PSTRG_SHADER_RANGE_START, PSTRG_SHADER_RANGE_SIZE},
}};
```

This makes the design intention explicit: some ranges exist purely to be persisted, while others (such as outfits/familiars) also update player state. 

---

### Performance Notes

- **Legacy approach**:
  Each save cycle rewrote all storages, regardless of whether they changed.
  On characters with thousands of storages, this caused unnecessary I/O and database load.
- **New approach (with PlayerStorage)**:
  - Tracks **only the keys that changed** (`m_modifiedKeys`) and **only the keys that were removed** (`m_removedKeys`).
  - `save()` performs:
    1. A single `DELETE` for all removed keys.
    2. A single `UPSERT` for all modified keys.
  - Keys untouched during the session are skipped, resulting in **smaller queries, fewer locks, and better scalability**.

This optimization significantly reduces save time during global save or player logout.

---

### Best Practices

- Always use `player.storage().add()` and `player.storage().get()` instead of manipulating maps directly.
- Call `remove(key)` explicitly when you want to delete a storage key.
- Although `add(key, -1)` is technically supported, prefer `remove()` for clarity and maintainability.
- Use `has()` to check for existence before assuming a key is present.
- Do **not** call `save()` manually after every change. Storages are automatically:
  - **Loaded on login** (`load()`).
  - **Saved on logout** (`save()`), persisting only keys that were actually modified or removed.
- This incremental approach ensures that logout remains efficient even for players with thousands of storages, while avoiding unnecessary writes during gameplay.

---

### Summary

`PlayerStorage` provides a **clean, efficient, and extensible** way to manage player storages.
It improves modularity, prevents direct map misuse, optimizes persistence, and integrates naturally with the rest of the game engine.
The recent refactoring of reserved ranges (into explicit **pass-through lists**) further improves code readability and clarifies the design intent for future contributors.
