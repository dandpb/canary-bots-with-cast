# Events

## Overview

Configures the XML-based entity event bindings (`events.xml`, being phased out in favor of Lua `EventCallback`) and delegates enabled `Creature`, `Party`, and `Player` event hooks to `./scripts/README.md`.

## Subdirectories & Boundaries

- [scripts](./scripts/README.md): Lua implementations for `Creature`, `Party`, and `Player` event callbacks enabled in `events.xml`.

## Interface

- `[events.xml:events]`: Enables C++-to-Lua event bindings for `Creature` (`onChangeOutfit`, `onDrainHealth`, `onTargetCombat`), `Party` (`onJoin`, `onLeave`, `onShareExperience`, `onDisband`), and `Player` (`onChangeZone`, `onChangeHazard`, `onGainExperience`, `onGainSkillTries`, `onItemMoved`, `onInventoryUpdate`, `onLookInBattleList`, `onMoveCreature`, `onMoveItem`, `onReportBug`, `onReportRuleViolation`, `onTradeRequest`, `onTurn`, `onCombat`; `onLoseExperience` is disabled with `enabled="0"`).
- [scripts](./scripts/README.md): Provides the `Creature:*`, `Party:*`, and `Player:*` method implementations.

## Invariants

- `[events.xml:event]`: Only `<event>` entries with `enabled="1"` are dispatched by the C++ engine (`Player:onLoseExperience` is `enabled="0"`).

## Side Effects

- Delegates combat, party hazard/XP sharing, item movement, stamina/XP calculation, and disk bug/violation reporting side effects to `./scripts/README.md`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
