# monk

## Overview
Package implementation for `data/scripts/spells/support/monk`, providing component logic and data interfaces for monk.

## Interface
- `spell.onCastSpell` (`[avatar_of_balance.lua:spell.onCastSpell]`)
- `onTargetCreature_BalancedBrawl` (`[balanced_brawl.lua:onTargetCreature_BalancedBrawl]`)
- `spell.onCastSpell` (`[balanced_brawl.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[focus_harmony.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[focus_serenity.lua:spell.onCastSpell]`)
- `onTargetCreature` (`[mentor_other.lua:onTargetCreature]`)
- `spell.onCastSpell` (`[mentor_other.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[virtue_of_harmony.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[virtue_of_justice.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[virtue_of_sustain.lua:spell.onCastSpell]`)

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[avatar_of_balance.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
