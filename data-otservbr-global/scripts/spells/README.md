# Spells

## Overview
Intermediate blueprint grouping 1 subdirectories under `scripts/spells`.

## Subdirectories & Boundaries
- [monster](./monster/README.md) - Component package under `scripts/spells/monster` containing 591 files (`abyssador_paralyze.lua`..`zushuka_paralyze.lua`).

## Interface
- Defines 591 script/configuration files (`abyssador_paralyze.lua` through `zushuka_paralyze.lua`) [abyssador_paralyze.lua]
- `spell.onCastSpell(creature, var)` [abyssador_paralyze.lua:spell.onCastSpell]
- [monster](./monster/README.md) - Component package under `scripts/spells/monster` containing 591 files (`abyssador_paralyze.lua`..`zushuka_paralyze.lua`).

## Invariants
- Combat parameters and area matrices (`combat:setParameter`, `combat:setArea`) constrain spell/attack target resolution [abyssador_paralyze.lua:combat]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [abyssador_paralyze.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
