# attack

## Overview
Package implementation for `data/scripts/spells/attack`, providing component logic and data interfaces for attack.

## Interface
- `onGetFormulaValues` (`[annihilation.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[annihilation.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[apprentice's_strike.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[apprentice's_strike.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[berserk.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[berserk.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[brutal_strike.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[brutal_strike.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[buzz.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[buzz.lua:spell.onCastSpell]`)
- Subdirectory [`./monk/README.md`](./monk/README.md) - Sub-package for monk

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[divine_grenade.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
