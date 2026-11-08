# Player Imbuements

## Overview
Manages item imbuement definitions, categories, and active decay timers (`Imbuements`, `Imbuement`, `BaseImbuement`, `CategoryImbuement`, `ImbuementDecay`), loading configuration from `XML/imbuements.xml` and tracking equipped item imbuement duration consumption.

## Interface
- `Imbuements` (`[imbuements.hpp:Imbuements]`, `[imbuements.cpp:Imbuements]`): XML loader (`loadFromXml`, `reload`) and lookup service (`getImbuement`, `getBaseByID`, `getCategoryByID`, `getImbuements`) for imbuement definitions.
- `Imbuement` (`[imbuements.hpp:Imbuement]`, `[imbuements.cpp:Imbuement]`): Represents a specific imbuement definition with stats, skills, combat damage/absorb values, element type, sound effect, required items, and `isSkill()` / `isSpecialSkill()` / `isStat()` / `isDamage()` / `isResist()` predicates.
- `BaseImbuement`, `CategoryImbuement` (`[imbuements.hpp:BaseImbuement]`, `[imbuements.hpp:CategoryImbuement]`): Metadata structs for imbuement tiers (price, protection cost, percent, duration, remove cost) and categories (ID, name, aggressive flag).
- `ImbuementDecay` (`[imbuements_decay.hpp:ImbuementDecay]`, `[imbuements_decay.cpp:ImbuementDecay]`): Singleton (`getInstance()`) scheduling periodic 1-second decay checks (`checkImbuementDecay`) for tracked items (`startImbuementDecay`, `stopImbuementDecay`).

## Invariants
- `ImbuementDecay` only decrements imbuement duration on an item while it is actively equipped in a valid player inventory slot (`CONST_SLOT_FIRST` to `CONST_SLOT_LAST`), and non-aggressive imbuements (`!categoryImbuement->agressive`) also require the player to be in fight (`CONDITION_INFIGHT`) and not in a protection zone (`ZONE_PROTECTION`) (`[imbuements_decay.cpp:ImbuementDecay::canDecayImbuement]`).
- When all imbuement slots on a tracked item reach duration `0`, the item is removed from `m_itemsToDecay` (`[imbuements_decay.cpp:ImbuementDecay::checkImbuementDecay]`).

## Side Effects
- Reads `XML/imbuements.xml` from disk (`[imbuements.cpp:Imbuements::loadFromXml]`).
- `ImbuementDecay` schedules a recurring 1000ms task on `g_dispatcher()`, mutates `Item` imbuement slot durations, and invokes `Player::onDeEquipInventory()` / `Player::onEquipInventory()` when an active imbuement expires (`[imbuements_decay.cpp:ImbuementDecay::startImbuementDecay]`, `[imbuements_decay.cpp:ImbuementDecay::checkImbuementDecay]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
