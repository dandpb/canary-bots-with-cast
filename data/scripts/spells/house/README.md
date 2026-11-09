# house

## Overview
Package implementation for `data/scripts/spells/house`, providing component logic and data interfaces for house.

## Interface
- `spell.onCastSpell` (`[edit_door_list.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[edit_guest_list.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[edit_subowner_list.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[kick.lua:spell.onCastSpell]`)

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
