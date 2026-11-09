# Combat

## Overview
Implements the core combat resolution engine (`Combat`, `AreaCombat`, `MatrixArea`, `MagicField`, and Lua callbacks), creature status conditions (`Condition` hierarchy), and spell registration/execution (`Spells`, `Spell`, `InstantSpell`, `RuneSpell`, `CombatSpell`).

## Interface
- `Combat` (`[combat.hpp:Combat]`): Executes health/mana/condition/dispel combat (`doCombat`, `doCombatHealth`, `doCombatMana`, `doCombatCondition`, `doCombatDispel`, `doCombatChain`), target/zone validation (`canDoCombat`, `canTargetCreature`, `isInPvpZone`, `isProtected`, `isPlayerCombat`), and Monk mechanics (`applyMantraAbsorb`, `harmonyHeal`).
- `CombatParams`, `AreaCombat`, `MatrixArea`, `MagicField` (`[combat.hpp:CombatParams]`, `[combat.hpp:AreaCombat]`, `[combat.hpp:MatrixArea]`, `[combat.hpp:MagicField]`): Area-of-effect matrices, combat parameters, and ground magic field items.
- `ValueCallback`, `TileCallback`, `TargetCallback`, `ChainCallback`, `ChainPickerCallback` (`[combat.hpp:ValueCallback]`, `[combat.hpp:TileCallback]`, `[combat.hpp:TargetCallback]`, `[combat.hpp:ChainCallback]`, `[combat.hpp:ChainPickerCallback]`): Lua script callbacks for damage calculation, tile/target effects, and chain combat targeting.
- `Condition` and derived classes (`[condition.hpp:Condition]`, `[condition.hpp:ConditionGeneric]`, `[condition.hpp:ConditionSerene]`, `[condition.hpp:ConditionAttributes]`, `[condition.hpp:ConditionRegeneration]`, `[condition.hpp:ConditionManaShield]`, `[condition.hpp:ConditionSoul]`, `[condition.hpp:ConditionInvisible]`, `[condition.hpp:ConditionDamage]`, `[condition.hpp:ConditionFeared]`, `[condition.hpp:ConditionSpeed]`, `[condition.hpp:ConditionOutfit]`, `[condition.hpp:ConditionLight]`, `[condition.hpp:ConditionSpellCooldown]`, `[condition.hpp:ConditionSpellGroupCooldown]`): Factory (`createCondition`), lifecycle (`startCondition`, `executeCondition`, `endCondition`, `addCondition`), and binary serialization (`serialize`, `unserialize`) for buffs, debuffs, DoTs, fear, speed, and cooldowns.
- `Spells`, `BaseSpell`, `CombatSpell`, `Spell`, `InstantSpell`, `RuneSpell` (`[spells.hpp:Spells]`, `[spells.hpp:BaseSpell]`, `[spells.hpp:CombatSpell]`, `[spells.hpp:Spell]`, `[spells.hpp:InstantSpell]`, `[spells.hpp:RuneSpell]`, `[spells.hpp:g_spells]`): Spell registry (`registerInstantLuaEvent`, `registerRuneLuaEvent`), lookup (`getInstantSpell`, `getRuneSpell`, `getSpellByName`), and casting (`playerSaySpell`, `castSpell`, `executeUse`).

## Invariants
- Protection zone and No-PvP zone rules are enforced by `Combat::canTargetCreature` and `Combat::canDoCombat` unless bypassed by `PlayerFlags_t::IgnoreProtectionZone` (`[combat.cpp:Combat::canTargetCreature]`, `[combat.cpp:Combat::canDoCombat]`).
- Bot players (`player->isBotPlayer()`) do not consume weapon charges during `COMBAT_FORMULA_SKILL` evaluation (`[combat.cpp:Combat::getCombatDamage]`) and bypass the `MAX_PLAYERS_OUTSIDE_PZ_PER_ACCOUNT` multi-client spell restriction (`[spells.cpp:Spells::playerSaySpell]`).
- Players with `CONDITION_FEARED` cannot cast spoken instant spells (`[spells.cpp:Spells::playerSaySpell]`), and `Combat::checkFearConditionAffected` caps concurrent fear conditions across party members (`[combat.hpp:Combat::checkFearConditionAffected]`).
- `Condition::executeCondition` (`[condition.cpp:Condition::executeCondition]`) treats `ticks == -1` as permanent and expires timed conditions once `getEndTime() < OTSYS_TIME()`.
- Duplicate instant spell words or rune item IDs are rejected during registration (`[spells.cpp:Spells::registerInstantLuaEvent]`, `[spells.cpp:Spells::registerRuneLuaEvent]`).

## Side Effects
- Mutates creature health, mana, soul, attributes, speed, outfit, light, and active conditions via `g_game()` (`[combat.cpp:Combat::CombatHealthFunc]`, `[combat.cpp:Combat::CombatManaFunc]`, `[condition.cpp:Condition::executeCondition]`).
- Transforms charged weapons/runes and spawns magic field items or sanctuary tiles on the map (`[combat.cpp:Combat::getCombatDamage]`, `[spells.cpp:applySanctuaryEffect]`).
- Invokes Lua script callbacks (`ValueCallback`, `TargetCallback`, `TileCallback`, `ChainCallback`, `ChainPickerCallback`, `InstantSpell::executeCastSpell`, `RuneSpell::executeCastSpell`) and emits network visual/sound effects to spectators (`[combat.cpp:Combat::sendCombatEffect]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
