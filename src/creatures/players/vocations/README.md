# vocations

## Overview
Package implementation for `src/creatures/players/vocations`, providing component logic and data interfaces for vocations.

## Interface
- `loadFromXml` (`[vocation.cpp:loadFromXml]`)
- `Vocation` (`[vocation.hpp:Vocation]`)
- `Vocations` (`[vocation.hpp:Vocations]`)
- `WheelGemQuality_t` (`[vocation.hpp:WheelGemQuality_t]`)
- `WheelGemSupremeModifier_t` (`[vocation.hpp:WheelGemSupremeModifier_t]`)
- `getTotalSkillTries` (`[vocation.hpp:getTotalSkillTries]`)
- `getReqSkillTries` (`[vocation.hpp:getReqSkillTries]`)
- `getTotalMana` (`[vocation.hpp:getTotalMana]`)
- `getReqMana` (`[vocation.hpp:getReqMana]`)

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[vocation.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
