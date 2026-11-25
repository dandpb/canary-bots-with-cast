# attack

## Overview
Package implementation for `data/scripts/spells/attack`, providing 69 attack spell scripts (`annihilation.lua`..`wrath_of_nature.lua`, including Monk spells moved from `monk/` and `practise_fire_wave.lua`).

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
- Additional attack & Monk spells (`[chained_penance.lua]`, `[devastating_knockout.lua]`, `[double_jab.lua]`, `[flurry_of_blows.lua]`, `[forceful_uppercut.lua]`, `[greater_flurry_of_blows.lua]`, `[greater_tiger_clash.lua]`, `[lesser_ethereal_spear.lua]`, `[lesser_front_sweep.lua]`, `[mystic_repulse.lua]`, `[practise_fire_wave.lua]`, `[spiritual_outburst.lua]`, `[sweeping_takedown.lua]`, `[swift_jab.lua]`, `[tiger_clash.lua]`, and remaining `*.lua` spell files).

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[divine_grenade.lua]`)

## Verification
- See the [Lua regression guide](../../../../tests/lua/README.md).
