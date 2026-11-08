# support

## Overview
Package implementation for `data/scripts/spells/support`, providing component logic and data interfaces for support.

## Interface
- `spell.onCastSpell` (`[avatar_of_light.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[avatar_of_nature.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[avatar_of_steel.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[avatar_of_storm.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[blood_rage.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[cancel_invisibility.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[cancel_magic_shield.lua:spell.onCastSpell]`)
- `onTargetCreature` (`[challenge.lua:onTargetCreature]`)
- `spell.onCastSpell` (`[challenge.lua:spell.onCastSpell]`)
- `spell.onCastSpell` (`[charge.lua:spell.onCastSpell]`)
- Subdirectory [`./monk/README.md`](./monk/README.md) - Sub-package for monk

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[avatar_of_light.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[avatar_of_nature.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[avatar_of_steel.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[avatar_of_storm.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[divine_empowerment.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
