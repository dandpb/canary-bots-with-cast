# Expert PvP Component (`src/creatures/players/components/pvp`)

## Overview
Implements the Expert PvP and Retro PvP evaluation rules (`ExpertPvp`), per-player PvP mode state (`PlayerPvp`), relation classification, combat/walkthrough/field-step/field-damage decision models, situational mark resolution, and cast-time field context metadata.

## Interface
- `ExpertPvpModeSource`, `ExpertPvpRelation`, `ExpertPvpActionKind`, `ExpertPvpDecisionReason`, `ExpertPvpSkullAction`, `ExpertPvpSituationMark` (`[expert_pvp_definitions.hpp:ExpertPvpModeSource]`, `[expert_pvp_definitions.hpp:ExpertPvpRelation]`, `[expert_pvp_definitions.hpp:ExpertPvpActionKind]`): Core enums for PvP mode provenance, actor-subject relations, actions, decision reasons, skull actions, and situation marks.
- `ExpertPvpModeResult`, `ExpertPvpRelationContext`, `ExpertPvpRelationResult`, `ExpertPvpSituation`, `ExpertPvpDecision`, `ExpertPvpWalkthroughDecision`, `ExpertFieldContext`, `ExpertPvpFieldStepDecision`, `ExpertPvpFieldDamageDecision`, `ExpertPvpFieldVisualDecision` (`[expert_pvp_definitions.hpp:ExpertPvpDecision]`, `[expert_pvp_definitions.hpp:ExpertFieldContext]`): Value structs carrying classification facts, combat/field/walkthrough/visual decisions, and field cast context.
- `ExpertPvp` (`[expert_pvp.hpp:ExpertPvp]`, `[expert_pvp.cpp:ExpertPvp::isEnabled]`): Non-instantiable static rule engine providing world-type checks (`isEnabled`, `isExpertPvpWorldType`, `isRetroPvpWorldType`), mode normalization (`defaultModeForClient`, `modeFromClientByte`, `normalizeMode`), relation classification (`classifyRelation`, `classifyFieldRelation`), action evaluation (`evaluateCombatAction`, `canWalkThrough`, `evaluateWalkthrough`, `evaluateFieldStep`, `evaluateFieldDamage`, `getFieldClientId`), mark management (`getSituationMark`, `getSituationCreatureMark`, `refreshCreatureMarkForViewer`, `refreshVisibleSituationMarks`, `refreshAllVisibleSituationMarks`), side-effect dispatch (`applyCombatSideEffects`, `applyFieldStepSideEffects`), and field context helpers (`isExpertFieldItem`, `makeFieldContext`, `getFieldContext`, `attachFieldContext`).
- `PlayerPvp` (`[player_pvp.hpp:PlayerPvp]`, `[player_pvp.cpp:PlayerPvp::setMode]`): Per-player PvP mode holder (`getMode`, `setMode`, `normalizeMode`, `isExpertPvpEnabled`, defaulting to `PVP_MODE_DOVE`).

## Invariants
- `ExpertPvp` is a static-only utility (`ExpertPvp() = delete`) whose decisions evaluate explicitly supplied `ExpertPvpRelationContext` / `ExpertFieldContext` snapshots (`[expert_pvp.hpp:ExpertPvp]`).
- `ExpertFieldContext` is considered valid only when `canonicalItemId != 0` (`[expert_pvp_definitions.hpp:ExpertFieldContext::operator bool]`).
- `PlayerPvp` initializes its stored mode to `PVP_MODE_DOVE` (`[player_pvp.hpp:PlayerPvp::m_mode]`).

## Side Effects
- `ExpertPvp::refreshCreatureMarkForViewer`, `refreshVisibleSituationMarks`, and `refreshAllVisibleSituationMarks` update visible creature situation marks for online players (`[expert_pvp.cpp:ExpertPvp::refreshAllVisibleSituationMarks]`).
- `ExpertPvp::applyCombatSideEffects` and `applyFieldStepSideEffects` apply skull, PZ-lock, fight, and square side effects determined by `ExpertPvpDecision` / `ExpertPvpFieldStepDecision` (`[expert_pvp.cpp:ExpertPvp::applyCombatSideEffects]`, `[expert_pvp.cpp:ExpertPvp::applyFieldStepSideEffects]`).
- `ExpertPvp::attachFieldContext` attaches cast-time owner mode and target/attacker snapshots to field `Item` instances (`[expert_pvp.cpp:ExpertPvp::attachFieldContext]`).

## Verification
- See the [C++ build and test guide](../../../../../tests/README.md#running-tests).
