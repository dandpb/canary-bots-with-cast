# healing

## Overview
Package implementation for `data/scripts/spells/healing`, providing component logic and data interfaces for healing.

## Interface
- `onGetFormulaValues` (`[bruise_bane.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[bruise_bane.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[cure_bleeding.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[cure_burning.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[cure_curse.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[cure_electrification.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[cure_poison.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[divine_healing.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[divine_healing.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[fair_wound_cleansing.lua:onGetFormulaValues]`)
- Subdirectory [`./monk/README.md`](./monk/README.md) - Sub-package for monk

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
