# Animus Mastery

## Overview
Manages a player's unlocked monster soul/animus masteries (`AnimusMastery`), calculating experience multipliers based on bestiary monster unlocks and persisting the unlocked monster race list to the player's key-value (`KV`) store.

## Interface
- `AnimusMastery` (`[animus_mastery.hpp:AnimusMastery]`, `[animus_mastery.cpp:AnimusMastery]`): Per-player component providing `add(const std::string &addMonsterType)`, `remove(const std::string &removeMonsterType)`, `has(const std::string &searchMonsterType) const`, `getPoints() const`, `getExpMultiplier() const`, `save() const`, and `load()`.

## Invariants
- `AnimusMastery::add` deduplicates entries and only inserts a monster name if `has(addMonsterType)` is false (`[animus_mastery.cpp:AnimusMastery::add]`).
- `getExpMultiplier()` computes a baseline `1.0f` plus `CONFIG_BASE_MULTIPLIER` (2.0%) and an additional `CONFIG_STEP_MULTIPLIER` (0.1%) per `CONFIG_MONSTERS_PER_MULTIPLIER` (10) unlocked animus masteries, capped at `CONFIG_MAX_MULTIPLIER` (4.0%) (`[animus_mastery.cpp:AnimusMastery::getExpMultiplier]`).

## Side Effects
- Reads and writes the `"animus_mastery"` array in the owning player's `KV` store during `load()` and `save()` (`[animus_mastery.cpp:AnimusMastery::load]`, `[animus_mastery.cpp:AnimusMastery::save]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
