# Wheel of Destiny Component

## Overview
Implements the player's Wheel of Destiny progression system, including slot point allocation across four elemental/domain quadrants, conviction/dedication/revelation perk calculation, promotion scroll unlocks, Atelier gem revelation/socket management, and gem modifier strategies.

## Interface
- `PlayerWheel` (`[player_wheel.hpp:PlayerWheel]`, `[player_wheel.cpp:PlayerWheel]`): Per-player component managing slot points (`loadDBPlayerSlotPointsOnLogin`, `saveDBPlayerSlotPointsOnLogout`, `saveSlotPointsOnPressSaveButton`, `canPlayerSelectPointOnSlot`), bonus calculation (`initializePlayerData`, `reloadPlayerData`, `registerPlayerBonusData`, `loadDedicationAndConvictionPerks`, `loadRevelationPerks`), combat/spell hooks (`onThink`, `checkAbilities`, `checkGiftOfLife`, `adjustDamageBasedOnResistanceAndSkill`, `calculateMitigation`, `getSpellBonus`), promotion scrolls (`unlockScroll`, `loadKVScrolls`, `saveKVScrolls`), and gem operations (`revealGem`, `destroyGem`, `switchGemDomain`, `toggleGemLock`, `setActiveGem`, `removeActiveGem`, `improveGemGrade`).
- `PlayerWheelGem` (`[player_wheel.hpp:PlayerWheelGem]`): Represents an individual revealed or active Wheel gem with UUID, lock status, affinity, quality, and basic/supreme modifiers (`save`, `remove`, `load`).
- `PromotionScroll` (`[player_wheel.hpp:PromotionScroll]`): Defines a promotion scroll item ID, scroll key name, and bonus wheel points.
- `WheelSlots_t`, `WheelStageEnum_t`, `WheelStagePointsEnum_t`, `WheelStage_t`, `WheelOnThink_t`, `WheelStat_t`, `WheelMajor_t`, `WheelInstant_t`, `WheelAvatarSkill_t`, `WheelSpellGrade_t`, `WheelSpellBoost_t` (`[wheel_definitions.hpp:WheelSlots_t]`, `[wheel_definitions.hpp:WheelStage_t]`, `[wheel_definitions.hpp:WheelStat_t]`, `[wheel_definitions.hpp:WheelInstant_t]`, `[wheel_definitions.hpp:WheelSpellGrade_t]`, `[wheel_definitions.hpp:WheelSpellBoost_t]`): Enumerations for Wheel slots (1–36), stage thresholds, stats, instants, and spell boosts.
- `PlayerWheelMethodsBonusData` (`[wheel_definitions.hpp:PlayerWheelMethodsBonusData]`): Aggregated passive and active Wheel bonus structure (stats, skills, leech, instant flags, stage tiers, avatar tiers, momentum, mitigation, and unlocked spells).
- `SlotInfo` (`[wheel_definitions.hpp:SlotInfo]`): Slot order, index, and point allocation tuple used during save validation and retry.
- `GemModifierStrategy`, `GemModifierResistanceStrategy`, `GemModifierStatStrategy`, `GemModifierRevelationStrategy`, `GemModifierSpellBonusStrategy`, `WheelModifierContext`, `WheelGemUtils` (`[wheel_gems.hpp:GemModifierStrategy]`, `[wheel_gems.hpp:WheelModifierContext]`, `[wheel_gems.hpp:WheelGemUtils]`, `[wheel_gems.cpp:WheelModifierContext]`): Strategy pattern and vocation lookup utilities for applying basic and supreme gem modifiers scaled by grade.
- `WheelSpells::Increase`, `WheelSpells::Decrease`, `WheelSpells::Leech`, `WheelSpells::Bonus` (`[wheel_spells.hpp:WheelSpells::Bonus]`): Structures describing per-spell Wheel upgrades (area, damage, heal, targets, cooldown, mana cost, leech).

## Invariants
- `m_minLevelToStartCountPoints` is 50 (`[player_wheel.hpp:m_minLevelToStartCountPoints]`); players only accumulate level-based Wheel points above level 50 at `WHEEL_POINTS_PER_LEVEL` (`[player_wheel.cpp:PlayerWheel::init]`), plus extra points from unlocked `PromotionScroll` entries (`[player_wheel.cpp:WheelOfDestinyPromotionScrolls]`).
- `m_wheelSlots` is 1-indexed across the 36 `WheelSlots_t` values (`[player_wheel.hpp:m_wheelSlots]`), and selecting points in deeper quadrant slots requires prerequisite adjacent slots and minimum quadrant point totals (`[player_wheel.cpp:PlayerWheel::canPlayerSelectPointOnSlot]`).
- Changing or decreasing allocated slot points requires the player to match `ownerId` and stand within temple range (`[player_wheel.hpp:PlayerWheel::getOptions]`).
- Gem modifier grades scale effect values by `1.0` (grade 0), `1.1` (grade 1), `1.2` (grade 2), or `1.5` (grade 3) (`[wheel_gems.cpp:WheelModifierContext::addStrategies]`).

## Side Effects
- Reads and writes player Wheel slot allocations in the database via `IOWheel` (`[player_wheel.hpp:PlayerWheel::loadDBPlayerSlotPointsOnLogin]`, `[player_wheel.hpp:PlayerWheel::saveDBPlayerSlotPointsOnLogout]`).
- Persists revealed/active gems, promotion scrolls, and modifier grades in the player's scoped `KV` store (`[player_wheel.hpp:PlayerWheelGem::save]`, `[player_wheel.hpp:PlayerWheel::saveActiveGems]`, `[player_wheel.hpp:PlayerWheel::saveKVScrolls]`, `[player_wheel.hpp:PlayerWheel::saveKVModGrades]`).
- Mutates owning `Player` combat stats, learned spells, conditions, health/mana/capacity, and sends Wheel UI/cooldown packets via `ProtocolGame` (`[player_wheel.hpp:PlayerWheel::reloadPlayerData]`, `[player_wheel.hpp:PlayerWheel::sendOpenWheelWindow]`, `[player_wheel.hpp:PlayerWheel::sendGiftOfLifeCooldown]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
