# Player Imbuements

## Overview
Manages item imbuement definitions, categories, and active decay timers (`Imbuements`, `Imbuement`, `BaseImbuement`, `CategoryImbuement`, `ImbuementDecay`), loading configuration from `XML/imbuements.xml` and tracking equipped item imbuement duration consumption.

## Interface
- `Imbuements` (`[imbuements.hpp:Imbuements]`, `[imbuements.cpp:Imbuements]`): XML loader (`loadFromXml`, `reload`) and lookup service (`getImbuement`, `getBaseByID`, `getCategoryByID`, `getImbuements`) for imbuement definitions.
- `Imbuement` (`[imbuements.hpp:Imbuement]`, `[imbuements.cpp:Imbuement]`): Represents a specific imbuement definition with stats, skills, combat damage/absorb values, element type, sound effect, required items, and `isSkill()` / `isSpecialSkill()` / `isStat()` / `isDamage()` / `isResist()` predicates.
- `BaseImbuement`, `CategoryImbuement` (`[imbuements.hpp:BaseImbuement]`, `[imbuements.hpp:CategoryImbuement]`): Metadata structs for imbuement tiers (price, protection cost, percent, duration, remove cost) and categories (ID, name, aggressive flag).
- `ImbuementDecay` (`[imbuements.hpp:ImbuementDecay]`, `[imbuements.cpp:ImbuementDecay]`): Singleton (`getInstance()`) scheduling periodic decay checks (`checkImbuementDecay`) for tracked items (`startImbuementDecay`, `stopImbuementDecay`).

## Invariants
- Decay requires a holding player. Aggressive imbuements and categories subject to `TOGGLE_IMBUEMENT_NON_AGGRESSIVE_FIGHT_ONLY` require combat outside protection zones and outside backpacks. A non-aggressive imbuement with a parent requires that parent to be the player (`[imbuements.cpp:ImbuementDecay::canDecayImbuement]`).
- Decay checks stop tracking an item when it has no active imbuements to process (`[imbuements.cpp:ImbuementDecay::checkImbuementDecay]`).

## Side Effects
- Reads `XML/imbuements.xml` from disk (`[imbuements.cpp:Imbuements::loadFromXml]`).
- `ImbuementDecay` schedules checks on `g_dispatcher()` and updates the durations of tracked imbuements (`[imbuements.cpp:ImbuementDecay::startImbuementDecay]`, `[imbuements.cpp:ImbuementDecay::checkImbuementDecay]`).

## Verification
- See the [C++ build and test guide](../../../../tests/README.md#running-tests).
