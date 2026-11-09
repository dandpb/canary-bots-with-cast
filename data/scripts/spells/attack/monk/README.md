# monk

## Overview
Package implementation for `data/scripts/spells/attack/monk`, providing component logic and data interfaces for monk.

## Interface
- `onGetFormulaValues` (`[chained_penance.lua:onGetFormulaValues]`)
- `canChain` (`[chained_penance.lua:canChain]`)
- `getChainValue` (`[chained_penance.lua:getChainValue]`)
- `spell.onCastSpell` (`[chained_penance.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[devastating_knockout.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[devastating_knockout.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[double_jab.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[double_jab.lua:spell.onCastSpell]`)
- `onGetFormulaValues` (`[flurry_of_blows.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[flurry_of_blows.lua:spell.onCastSpell]`)

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[spiritual_outburst.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
