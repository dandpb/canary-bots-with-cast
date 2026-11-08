# Oramond

## Overview
Component package under `raids/oramond` containing 2 files (`crustacea_gigantica_4.xml`..`crustacea_gigantica_5.xml`).

## Interface
- `<areaspawn>` monster `Crustacea Gigantica` (amount=1) [crustacea_gigantica_4.xml:areaspawn]
- `<areaspawn>` monster `Crustacea Gigantica` (amount=1) [crustacea_gigantica_5.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [crustacea_gigantica_4.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [crustacea_gigantica_5.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [crustacea_gigantica_4.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [crustacea_gigantica_5.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
