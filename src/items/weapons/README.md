# weapons

## Overview
Package implementation for `src/items/weapons`, providing component logic and data interfaces for weapons.

## Interface
- `sendWeaponSoundEffect` (`[weapons.cpp:sendWeaponSoundEffect]`)
- `Weapon` (`[weapons.hpp:Weapon]`)
- `WeaponMelee` (`[weapons.hpp:WeaponMelee]`)
- `WeaponDistance` (`[weapons.hpp:WeaponDistance]`)
- `WeaponWand` (`[weapons.hpp:WeaponWand]`)
- `LuaScriptInterface` (`[weapons.hpp:LuaScriptInterface]`)
- `Combat` (`[weapons.hpp:Combat]`)
- `Player` (`[weapons.hpp:Player]`)
- `Creature` (`[weapons.hpp:Creature]`)

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[weapons.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
