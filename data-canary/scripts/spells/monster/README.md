# monster

## Overview
Package implementation for `data-canary/scripts/spells/monster`, providing component logic and data interfaces for monster.

## Interface
- `spell.onCastSpell` (`[fury_skill_reducer.lua:spell.onCastSpell]`)
- `onTargetCreature` (`[summon_challenge.lua:onTargetCreature]`)
- `spell.onCastSpell` (`[summon_challenge.lua:spell.onCastSpell]`)

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
