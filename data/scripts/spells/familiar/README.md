# familiar

## Overview
Package implementation for `data/scripts/spells/familiar`, providing component logic and data interfaces for familiar.

## Interface
- `spell.onCastSpell` (`[druid_familiar.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[knight_familiar.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[paladin_familiar.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[sorcerer_familiar.lua:spell.onCastSpell]`)
- Subdirectory [`./monk/README.md`](./monk/README.md) - Sub-package for monk

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
