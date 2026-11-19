# Animus Mastery

## Overview
Manages a player's unlocked Animus Masteries, calculates an experience multiplier from the number of masteries, and serializes the unlocked monster names.

## Interface
- `AnimusMastery` (`[animus_mastery.hpp:AnimusMastery]`, `[animus_mastery.cpp:AnimusMastery]`): Per-player component with `add`, `remove`, `has`, `getPoints`, `getExperienceMultiplier`, `serialize`, and `unserialize`.

## Invariants
- `AnimusMastery::add` deduplicates entries and only inserts a monster name if `has(addMonsterType)` is false (`[animus_mastery.cpp:AnimusMastery::add]`).
- `getExperienceMultiplier()` adds the configured base percentage and a bonus for each full group of masteries, then caps the resulting multiplier at the configured maximum (`[animus_mastery.cpp:AnimusMastery::getExperienceMultiplier]`). `[animus_mastery.cpp:AnimusMastery::init]` loads these settings and clamps group size to at least one.

## Side Effects
- Reads and writes monster names through property streams (`[animus_mastery.cpp:AnimusMastery::serialize]`, `[animus_mastery.cpp:AnimusMastery::unserialize]`).

## Verification
- See the [C++ build and test guide](../../../../tests/README.md#running-tests).
