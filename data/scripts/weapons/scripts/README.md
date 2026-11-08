# scripts

## Overview
Package implementation for `data/scripts/weapons/scripts`, providing component logic and data interfaces for scripts.

## Interface
- `onGetFormulaValues` (`[diamond_arrow.lua:onGetFormulaValues]`)
- `diamondArrow.onUseWeapon` (`[diamond_arrow.lua:diamondArrow.onUseWeapon]`)
- `poisonArrow.onUseWeapon` (`[poison_arrow.lua:poisonArrow.onUseWeapon]`)
- `viperStar.onUseWeapon` (`[viper_star.lua:viperStar.onUseWeapon]`)

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
