# combat

## Overview
Package implementation for `src/lua/functions/creatures/combat`, providing component logic and data interfaces for combat.

## Interface
- `CombatFunctions` (`[combat_functions.hpp:CombatFunctions]`)
- `init` (`[combat_functions.hpp:init]`)
- `luaCombatCreate` (`[combat_functions.hpp:luaCombatCreate]`)
- `luaCombatSetParameter` (`[combat_functions.hpp:luaCombatSetParameter]`)
- `luaCombatSetFormula` (`[combat_functions.hpp:luaCombatSetFormula]`)
- `luaCombatSetArea` (`[combat_functions.hpp:luaCombatSetArea]`)
- `luaCombatSetCondition` (`[combat_functions.hpp:luaCombatSetCondition]`)
- `luaCombatSetCallback` (`[combat_functions.hpp:luaCombatSetCallback]`)
- `ConditionFunctions` (`[condition_functions.hpp:ConditionFunctions]`)
- `init` (`[condition_functions.hpp:init]`)

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[spell_functions.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
