# healing

## Overview
Package implementation for `data/scripts/spells/healing`, providing 28 healing spell scripts (`bruise_bane.lua`..`wound_cleansing.lua`, including Monk healing spells and `practise_healing.lua`).

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
- Additional healing & Monk spells (`[mass_spirit_mend.lua]`, `[practise_healing.lua]`, `[restore_balance.lua]`, `[spirit_mend.lua]`, and remaining `*.lua` spell files).

## Invariants
- None

## Side Effects
- None

## Verification
- See the [Lua regression guide](../../../../tests/lua/README.md).
