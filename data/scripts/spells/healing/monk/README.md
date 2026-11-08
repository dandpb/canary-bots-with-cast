# monk

## Overview
Package implementation for `data/scripts/spells/healing/monk`, providing component logic and data interfaces for monk.

## Interface
- `onTargetCreature` (`[mass_spirit_mend.lua:onTargetCreature]`)
- `onTargetCreatureWOD` (`[mass_spirit_mend.lua:onTargetCreatureWOD]`)
- `spell.onCastSpell` (`[mass_spirit_mend.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[restore_balance.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[restore_balance.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[spirit_mend.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[spirit_mend.lua:spell.onCastSpell]`)

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
