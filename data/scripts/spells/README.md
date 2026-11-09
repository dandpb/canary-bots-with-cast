# spells

## Overview
Package implementation for `data/scripts/spells`, providing component logic and data interfaces for spells.

## Interface
- `onGetFormulaValues` (`[#example.lua:onGetFormulaValues]`)
- `spell.onCastSpell` (`[#example.lua:spell.onCastSpell]`)
- `conjureRune.onCastSpell` (`[#example.lua:conjureRune.onCastSpell]`)
- Subdirectory [`./attack/README.md`](./attack/README.md) - Sub-package for attack
- Subdirectory [`./conjuring/README.md`](./conjuring/README.md) - Sub-package for conjuring
- Subdirectory [`./familiar/README.md`](./familiar/README.md) - Sub-package for familiar
- Subdirectory [`./healing/README.md`](./healing/README.md) - Sub-package for healing
- Subdirectory [`./house/README.md`](./house/README.md) - Sub-package for house
- Subdirectory [`./party/README.md`](./party/README.md) - Sub-package for party
- Subdirectory [`./support/README.md`](./support/README.md) - Sub-package for support

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
